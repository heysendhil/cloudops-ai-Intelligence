import json
from pathlib import Path

import pytest

from app.tools.kubernetes_parser import extract_kubernetes_reliability

FIXTURE_K8S = {
    "cluster": "test-cluster",
    "namespace": "test-ns",
    "snapshot_time": "2026-01-01T00:00:00Z",
    "deployment": {
        "name": "test-api",
        "desired_replicas": 3,
        "available_replicas": 2,
        "liveness_probe": {"httpGet": {"path": "/health", "port": 8080}, "periodSeconds": 10},
        "readiness_probe": {"httpGet": {"path": "/ready", "port": 8080}, "periodSeconds": 10},
    },
    "pods": [
        {
            "name": "test-api-1",
            "node": "node-a",
            "phase": "Running",
            "ready": True,
            "restart_count": 0,
            "restarts": [],
        },
        {
            "name": "test-api-2",
            "node": "node-b",
            "phase": "Running",
            "ready": True,
            "restart_count": 1,
            "restarts": [{"time": "2026-01-01T00:05:00Z", "reason": "Liveness probe failed", "exit_code": 137}],
        },
        {
            "name": "test-api-3",
            "node": "node-a",
            "phase": "Running",
            "ready": False,
            "restart_count": 0,
            "restarts": [],
        },
    ],
    "events": [
        {
            "time": "2026-01-01T00:04:40Z",
            "type": "Warning",
            "reason": "Unhealthy",
            "involved_object": "pod/test-api-2",
            "source": "kubelet",
            "message": "Liveness probe failed: HTTP probe failed with statuscode: 500",
        },
        {
            "time": "2026-01-01T00:04:50Z",
            "type": "Warning",
            "reason": "Unhealthy",
            "involved_object": "pod/test-api-2",
            "source": "kubelet",
            "message": "Liveness probe failed: HTTP probe failed with statuscode: 500",
        },
        {
            "time": "2026-01-01T00:05:00Z",
            "type": "Normal",
            "reason": "Killing",
            "involved_object": "pod/test-api-2",
            "source": "kubelet",
            "message": "Container test-api failed liveness probe, will be restarted",
        },
    ],
}


@pytest.fixture()
def fixture_k8s_path(tmp_path: Path) -> Path:
    k8s_file = tmp_path / "fixture-k8s.json"
    k8s_file.write_text(json.dumps(FIXTURE_K8S))
    return k8s_file


# --- deployment replica counts -------------------------------------------


def test_desired_replicas_exact_value(fixture_k8s_path: Path) -> None:
    result = extract_kubernetes_reliability(fixture_k8s_path)

    assert result.desired_replicas.available is True
    assert result.desired_replicas.value == 3
    assert result.desired_replicas.source_field == "deployment.desired_replicas"


def test_available_replicas_exact_value(fixture_k8s_path: Path) -> None:
    result = extract_kubernetes_reliability(fixture_k8s_path)

    assert result.available_replicas.available is True
    assert result.available_replicas.value == 2


def test_ready_replicas_is_computed_from_pods(fixture_k8s_path: Path) -> None:
    result = extract_kubernetes_reliability(fixture_k8s_path)

    assert result.ready_replicas.available is True
    assert result.ready_replicas.value == 2  # test-api-1 and test-api-2 are ready
    assert result.ready_replicas.source_field == "computed from pods[].ready"


def test_desired_replicas_missing_field_is_unavailable_not_invented(tmp_path: Path) -> None:
    data = json.loads(json.dumps(FIXTURE_K8S))
    del data["deployment"]["desired_replicas"]
    k8s_file = tmp_path / "no-desired.json"
    k8s_file.write_text(json.dumps(data))

    result = extract_kubernetes_reliability(k8s_file)

    assert result.desired_replicas.available is False
    assert result.desired_replicas.value is None
    assert result.desired_replicas.reason_unavailable is not None


def test_ready_replicas_unavailable_when_no_pods(tmp_path: Path) -> None:
    data = json.loads(json.dumps(FIXTURE_K8S))
    data["pods"] = []
    k8s_file = tmp_path / "no-pods.json"
    k8s_file.write_text(json.dumps(data))

    result = extract_kubernetes_reliability(k8s_file)

    assert result.ready_replicas.available is False
    assert result.ready_replicas.value is None


# --- pod status ------------------------------------------------------------


def test_pod_status_exact_values(fixture_k8s_path: Path) -> None:
    result = extract_kubernetes_reliability(fixture_k8s_path)

    assert len(result.pod_status) == 3
    statuses = {p.name: (p.phase, p.ready, p.node) for p in result.pod_status}
    assert statuses["test-api-1"] == ("Running", True, "node-a")
    assert statuses["test-api-2"] == ("Running", True, "node-b")
    assert statuses["test-api-3"] == ("Running", False, "node-a")


# --- pod restart counts -----------------------------------------------


def test_pod_restart_counts_exact_values(fixture_k8s_path: Path) -> None:
    result = extract_kubernetes_reliability(fixture_k8s_path)

    counts = {p.name: p.restart_count for p in result.pod_restart_counts}
    assert counts == {"test-api-1": 0, "test-api-2": 1, "test-api-3": 0}

    restarted = next(p for p in result.pod_restart_counts if p.name == "test-api-2")
    assert restarted.restarts == [
        {"time": "2026-01-01T00:05:00Z", "reason": "Liveness probe failed", "exit_code": 137}
    ]


# --- events ------------------------------------------------------------


def test_events_are_returned_verbatim(fixture_k8s_path: Path) -> None:
    result = extract_kubernetes_reliability(fixture_k8s_path)

    assert len(result.events) == 3
    assert result.events[0].reason == "Unhealthy"
    assert result.events[0].involved_object == "pod/test-api-2"
    assert result.events[2].reason == "Killing"


def test_events_empty_when_not_present(tmp_path: Path) -> None:
    data = json.loads(json.dumps(FIXTURE_K8S))
    del data["events"]
    k8s_file = tmp_path / "no-events.json"
    k8s_file.write_text(json.dumps(data))

    result = extract_kubernetes_reliability(k8s_file)

    assert result.events == []


# --- health probe findings --------------------------------------------


def test_health_probe_findings_one_per_pod(fixture_k8s_path: Path) -> None:
    result = extract_kubernetes_reliability(fixture_k8s_path)

    assert len(result.health_probe_findings) == 3
    findings_by_pod = {f.pod: f for f in result.health_probe_findings}

    assert findings_by_pod["test-api-1"].restart_triggered is False
    assert findings_by_pod["test-api-1"].probe_failure_events == []

    assert findings_by_pod["test-api-2"].restart_triggered is True
    assert len(findings_by_pod["test-api-2"].probe_failure_events) == 2
    assert all(
        e["involved_object"] == "pod/test-api-2"
        for e in findings_by_pod["test-api-2"].probe_failure_events
    )


def test_health_probe_findings_include_probe_config(fixture_k8s_path: Path) -> None:
    result = extract_kubernetes_reliability(fixture_k8s_path)

    finding = result.health_probe_findings[0]
    assert finding.liveness_probe_config == {
        "httpGet": {"path": "/health", "port": 8080},
        "periodSeconds": 10,
    }
    assert finding.readiness_probe_config == {
        "httpGet": {"path": "/ready", "port": 8080},
        "periodSeconds": 10,
    }


def test_health_probe_findings_never_invent_events_for_healthy_pods(
    fixture_k8s_path: Path,
) -> None:
    result = extract_kubernetes_reliability(fixture_k8s_path)

    for finding in result.health_probe_findings:
        if not finding.restart_triggered:
            assert finding.probe_failure_events == []


# --- file handling -------------------------------------------------------


def test_missing_kubernetes_file_raises_file_not_found(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist.json"

    with pytest.raises(FileNotFoundError):
        extract_kubernetes_reliability(missing_path)


def test_result_to_dict_is_json_serializable(fixture_k8s_path: Path) -> None:
    result = extract_kubernetes_reliability(fixture_k8s_path)

    serialized = json.dumps(result.to_dict())
    assert "pod_status" in serialized
    assert "health_probe_findings" in serialized


# --- real Phase 3 incident data: known exact values ------------------------


def test_real_incident_kubernetes_exact_values() -> None:
    result = extract_kubernetes_reliability()

    assert result.namespace == "payments"
    assert result.desired_replicas.value == 6
    assert result.available_replicas.value == 6
    assert result.ready_replicas.value == 6
    assert len(result.pod_status) == 6
    assert len(result.events) == 28

    restart_counts = {p.name: p.restart_count for p in result.pod_restart_counts}
    assert sum(restart_counts.values()) == 4
    assert restart_counts["payment-api-7f9c9d6b78-x4k2p"] == 1
    assert restart_counts["payment-api-7f9c9d6b78-h5f7r"] == 0


def test_real_incident_kubernetes_health_probe_findings() -> None:
    result = extract_kubernetes_reliability()

    restarted_findings = [f for f in result.health_probe_findings if f.restart_triggered]
    healthy_findings = [f for f in result.health_probe_findings if not f.restart_triggered]

    assert len(restarted_findings) == 4
    assert len(healthy_findings) == 2
    for finding in restarted_findings:
        assert len(finding.probe_failure_events) == 3
    for finding in healthy_findings:
        assert finding.probe_failure_events == []
