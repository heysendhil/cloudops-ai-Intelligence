import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

INCIDENT_PATH = DATA_DIR / "incidents" / "INC-2026-0912.json"
LOG_PATH = DATA_DIR / "logs" / "payment-api.log"
METRICS_PATH = DATA_DIR / "metrics" / "payment-api.json"
KUBERNETES_PATH = DATA_DIR / "kubernetes" / "payment-api.json"
RUNBOOK_PATH = DATA_DIR / "runbooks" / "database-connection-pool.md"


def _parse_iso(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


@pytest.fixture(scope="module")
def incident() -> dict:
    return json.loads(INCIDENT_PATH.read_text())


@pytest.fixture(scope="module")
def metrics() -> dict:
    return json.loads(METRICS_PATH.read_text())


@pytest.fixture(scope="module")
def kubernetes_state() -> dict:
    return json.loads(KUBERNETES_PATH.read_text())


@pytest.fixture(scope="module")
def log_lines() -> list[str]:
    return LOG_PATH.read_text().splitlines()


# --- incident record -------------------------------------------------------


def test_incident_json_has_required_fields(incident: dict) -> None:
    required_top_level = {
        "incident_id",
        "title",
        "service",
        "environment",
        "platform",
        "severity",
        "status",
        "detected_at",
        "time_window",
        "symptoms",
        "evidence_sources",
    }
    assert required_top_level.issubset(incident.keys())


def test_incident_matches_spec(incident: dict) -> None:
    assert incident["incident_id"] == "INC-2026-0912"
    assert incident["service"]["name"] == "Payment API"
    assert incident["service"]["slug"] == "payment-api"
    assert incident["environment"] == "production"
    assert incident["platform"] == "Kubernetes on AWS"
    assert incident["severity"] == "SEV-2"
    assert len(incident["symptoms"]) >= 4


def test_incident_time_window_is_ordered(incident: dict) -> None:
    start = _parse_iso(incident["time_window"]["start"])
    end = _parse_iso(incident["time_window"]["end"])
    detected_at = _parse_iso(incident["detected_at"])

    assert start < end
    assert start <= detected_at <= end


def test_incident_evidence_source_paths_exist(incident: dict) -> None:
    sources = incident["evidence_sources"]

    assert (REPO_ROOT / sources["logs"]).is_file()
    assert (REPO_ROOT / sources["metrics"]).is_file()
    assert (REPO_ROOT / sources["kubernetes"]).is_file()
    for runbook in sources["related_runbooks"]:
        assert (REPO_ROOT / runbook).is_file()


# --- metrics -----------------------------------------------------------


def test_metrics_json_has_required_structure(metrics: dict) -> None:
    assert metrics["service"] == "payment-api"
    assert metrics["incident_id"] == "INC-2026-0912"
    assert isinstance(metrics["datapoints"], list)
    assert len(metrics["datapoints"]) >= 10


def test_metrics_datapoints_are_chronologically_sorted(metrics: dict) -> None:
    timestamps = [_parse_iso(point["timestamp"]) for point in metrics["datapoints"]]

    assert timestamps == sorted(timestamps)


def test_metrics_datapoints_are_internally_consistent(metrics: dict) -> None:
    pool_max = metrics["db_pool"]["cluster_max_size"]
    previous_restarts = 0

    for point in metrics["datapoints"]:
        assert point["db_pool_active"] + point["db_pool_idle"] == pool_max
        assert point["http_2xx_count"] + point["http_5xx_count"] == point["request_count"]

        expected_utilization = round(point["db_pool_active"] / pool_max * 100, 1)
        assert abs(point["db_pool_utilization_pct"] - expected_utilization) < 0.2

        # pod restarts must never decrease over time
        assert point["pod_restart_count_cumulative"] >= previous_restarts
        previous_restarts = point["pod_restart_count_cumulative"]


def test_metrics_show_database_pressure_evidence(metrics: dict) -> None:
    baseline = metrics["datapoints"][0]
    peak_utilization = max(p["db_pool_utilization_pct"] for p in metrics["datapoints"])
    peak_5xx = max(p["http_5xx_count"] for p in metrics["datapoints"])
    final_restarts = metrics["datapoints"][-1]["pod_restart_count_cumulative"]

    assert baseline["db_pool_utilization_pct"] < 30
    assert peak_utilization == 100.0
    assert peak_5xx > baseline["http_5xx_count"] * 50
    assert 0 < final_restarts < 6  # "some" pods restarted, not all


def test_metrics_latency_peaks_near_four_seconds(metrics: dict) -> None:
    peak_latency = max(p["latency_ms_avg"] for p in metrics["datapoints"])

    assert 3500 <= peak_latency <= 4500


def test_metrics_db_cpu_present_and_peaks_near_92_pct(metrics: dict) -> None:
    baseline = metrics["datapoints"][0]
    peak_db_cpu = max(p["db_cpu_utilization_pct"] for p in metrics["datapoints"])

    assert baseline["db_cpu_utilization_pct"] < 30
    assert 88 <= peak_db_cpu <= 95


def test_metrics_db_cpu_exceeds_pod_cpu_at_peak(metrics: dict) -> None:
    # The database, not the application pods, is the bottleneck: DB CPU should
    # run hotter than pod CPU at the worst point of the incident.
    peak_point = max(metrics["datapoints"], key=lambda p: p["db_cpu_utilization_pct"])

    assert peak_point["db_cpu_utilization_pct"] > peak_point["cpu_utilization_pct"]


def test_metrics_http_5xx_rate_peaks_near_8_7_pct(metrics: dict) -> None:
    rates = [p["http_5xx_count"] / p["request_count"] * 100 for p in metrics["datapoints"]]
    peak_rate = max(rates)

    assert 8.0 <= peak_rate <= 9.5


def test_metrics_recovers_toward_baseline_by_end_of_window(metrics: dict) -> None:
    baseline = metrics["datapoints"][0]
    final = metrics["datapoints"][-1]

    assert final["db_pool_utilization_pct"] < 30
    assert final["latency_ms_avg"] < 300
    assert abs(final["latency_ms_avg"] - baseline["latency_ms_avg"]) < 50


# --- kubernetes state --------------------------------------------------


def test_kubernetes_json_has_required_structure(kubernetes_state: dict) -> None:
    assert kubernetes_state["namespace"] == "payments"
    assert kubernetes_state["deployment"]["name"] == "payment-api"
    assert isinstance(kubernetes_state["pods"], list)
    assert isinstance(kubernetes_state["events"], list)


def test_kubernetes_pod_count_matches_desired_replicas(kubernetes_state: dict) -> None:
    assert len(kubernetes_state["pods"]) == kubernetes_state["deployment"]["desired_replicas"]


def test_kubernetes_no_deploy_during_incident_window(kubernetes_state: dict) -> None:
    deployment_image = kubernetes_state["deployment"]["image"]
    deployment_replicaset = kubernetes_state["deployment"]["replicaset"]

    for pod in kubernetes_state["pods"]:
        assert pod["image"] == deployment_image
        assert pod["replicaset"] == deployment_replicaset


def test_kubernetes_restart_total_matches_metrics_peak(
    kubernetes_state: dict, metrics: dict
) -> None:
    total_pod_restarts = sum(pod["restart_count"] for pod in kubernetes_state["pods"])
    final_metrics_restarts = metrics["datapoints"][-1]["pod_restart_count_cumulative"]

    assert total_pod_restarts == final_metrics_restarts
    restarted_pods = [pod for pod in kubernetes_state["pods"] if pod["restart_count"] > 0]
    assert 0 < len(restarted_pods) < len(kubernetes_state["pods"])


def test_kubernetes_events_contain_liveness_failures(kubernetes_state: dict) -> None:
    unhealthy_events = [
        event for event in kubernetes_state["events"] if event["reason"] == "Unhealthy"
    ]

    assert len(unhealthy_events) > 0
    assert all("Liveness probe failed" in event["message"] for event in unhealthy_events)


def test_kubernetes_each_restarted_pod_has_a_killing_event(kubernetes_state: dict) -> None:
    killing_targets = {
        event["involved_object"]
        for event in kubernetes_state["events"]
        if event["reason"] == "Killing"
    }

    for pod in kubernetes_state["pods"]:
        if pod["restart_count"] > 0:
            assert f"pod/{pod['name']}" in killing_targets


# --- log file ------------------------------------------------------------


def test_log_file_is_not_json_or_markdown(log_lines: list[str]) -> None:
    first_line = log_lines[0].strip()

    assert not first_line.startswith("{")
    assert not first_line.startswith("[")
    assert not first_line.startswith("#")
    with pytest.raises(json.JSONDecodeError):
        json.loads(LOG_PATH.read_text())


def test_log_file_contains_database_pressure_evidence(log_lines: list[str]) -> None:
    full_text = "\n".join(log_lines)

    assert "HikariPool" in full_text
    assert "CannotGetJdbcConnectionException" in full_text
    assert "Connection is not available, request timed out" in full_text
    assert "utilization=100%" in full_text
    assert "responded 500" in full_text


def test_log_file_shows_pod_restart_boot_sequence(log_lines: list[str]) -> None:
    full_text = "\n".join(log_lines)

    assert "Received SIGTERM signal" in full_text
    assert "Starting PaymentApiApplication" in full_text
    assert "Started PaymentApiApplication" in full_text


def test_log_file_pod_names_match_kubernetes_pods(
    log_lines: list[str], kubernetes_state: dict
) -> None:
    full_text = "\n".join(log_lines)

    for pod in kubernetes_state["pods"]:
        assert pod["name"] in full_text


def test_log_file_timestamps_within_incident_window(log_lines: list[str], incident: dict) -> None:
    # Sub-second log timestamps vs. a round-minute window boundary can differ
    # by a fraction of a second without being inconsistent; allow a small buffer.
    boundary_tolerance = timedelta(seconds=5)
    window_start = _parse_iso(incident["time_window"]["start"]) - boundary_tolerance
    window_end = _parse_iso(incident["time_window"]["end"]) + boundary_tolerance

    timestamped_lines = [line for line in log_lines if line.startswith("payment-api-")]
    for line in timestamped_lines:
        parts = line.split()
        # format: <pod-name> <yyyy-MM-dd> <HH:mm:ss.SSS> ...
        date_str, time_str = parts[1], parts[2]
        line_time = datetime.strptime(
            f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S.%f"
        ).replace(tzinfo=timezone.utc)

        assert window_start <= line_time <= window_end


# --- runbook ---------------------------------------------------------------


def test_runbook_is_markdown_with_expected_sections() -> None:
    text = RUNBOOK_PATH.read_text()

    assert text.startswith("# Runbook: Database Connection Pool Exhaustion")
    for heading in [
        "## Symptoms",
        "## Likely Causes",
        "## Diagnosis Steps",
        "## Mitigation",
        "## Prevention",
    ]:
        assert heading in text


def test_runbook_references_the_incident() -> None:
    text = RUNBOOK_PATH.read_text()

    assert "INC-2026-0912" in text
