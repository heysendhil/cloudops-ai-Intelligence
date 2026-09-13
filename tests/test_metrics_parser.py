import json
from pathlib import Path

import pytest

from app.tools.metrics_parser import extract_cloud_metrics

FIXTURE_METRICS = {
    "service": "test-service",
    "window": {"start": "2026-01-01T00:00:00Z", "end": "2026-01-01T00:10:00Z"},
    "db_pool": {"cluster_max_size": 50},
    "datapoints": [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "request_count": 1000,
            "http_5xx_count": 10,
            "db_cpu_utilization_pct": 20,
            "db_pool_utilization_pct": 15.0,
            "db_pool_active": 8,
            "cpu_utilization_pct": 30,
            "memory_utilization_pct": 40,
            "latency_ms_avg": 100,
        },
        {
            "timestamp": "2026-01-01T00:05:00Z",
            "request_count": 800,
            "http_5xx_count": 80,
            "db_cpu_utilization_pct": 90,
            "db_pool_utilization_pct": 99.0,
            "db_pool_active": 49,
            "cpu_utilization_pct": 70,
            "memory_utilization_pct": 85,
            "latency_ms_avg": 3000,
        },
    ],
}


@pytest.fixture()
def fixture_metrics_path(tmp_path: Path) -> Path:
    metrics_file = tmp_path / "fixture-metrics.json"
    metrics_file.write_text(json.dumps(FIXTURE_METRICS))
    return metrics_file


# --- exact-value extraction tests -------------------------------------


def test_database_cpu_exact_values(fixture_metrics_path: Path) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    assert result.database_cpu.available is True
    assert result.database_cpu.unit == "percent"
    assert result.database_cpu.source_field == "db_cpu_utilization_pct"
    assert [p.value for p in result.database_cpu.points] == [20, 90]
    assert [p.timestamp for p in result.database_cpu.points] == [
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:05:00Z",
    ]


def test_database_connections_exact_values(fixture_metrics_path: Path) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    assert result.database_connections.available is True
    assert [p.value for p in result.database_connections.points] == [15.0, 99.0]


def test_connection_limit_exact_value(fixture_metrics_path: Path) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    assert result.connection_limit.available is True
    assert result.connection_limit.value == 50
    assert result.connection_limit.unit == "connections"
    assert result.connection_limit.source_field == "db_pool.cluster_max_size"


def test_active_connections_exact_values(fixture_metrics_path: Path) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    assert [p.value for p in result.active_connections.points] == [8, 49]


def test_application_cpu_exact_values(fixture_metrics_path: Path) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    assert [p.value for p in result.application_cpu.points] == [30, 70]


def test_application_memory_exact_values(fixture_metrics_path: Path) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    assert [p.value for p in result.application_memory.points] == [40, 85]


def test_request_latency_exact_values(fixture_metrics_path: Path) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    assert [p.value for p in result.request_latency.points] == [100, 3000]


def test_http_5xx_percentage_is_computed_exactly(fixture_metrics_path: Path) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    assert result.http_5xx_percentage.available is True
    assert result.http_5xx_percentage.unit == "percent"
    assert result.http_5xx_percentage.source_field == "http_5xx_count / request_count"
    # 10/1000*100 = 1.0, 80/800*100 = 10.0
    assert [p.value for p in result.http_5xx_percentage.points] == [1.0, 10.0]


# --- "never invent missing metrics" tests -------------------------------


def test_database_memory_is_reported_as_unavailable_not_invented(
    fixture_metrics_path: Path,
) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    assert result.database_memory.available is False
    assert result.database_memory.points == []
    assert result.database_memory.source_field is None
    assert result.database_memory.reason_unavailable is not None


def test_query_latency_is_reported_as_unavailable_not_invented(
    fixture_metrics_path: Path,
) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    assert result.query_latency.available is False
    assert result.query_latency.points == []
    assert result.query_latency.source_field is None
    assert result.query_latency.reason_unavailable is not None


def test_missing_connection_limit_is_reported_as_unavailable(tmp_path: Path) -> None:
    data = dict(FIXTURE_METRICS)
    data["db_pool"] = {}  # no cluster_max_size at all
    metrics_file = tmp_path / "no-limit.json"
    metrics_file.write_text(json.dumps(data))

    result = extract_cloud_metrics(metrics_file)

    assert result.connection_limit.available is False
    assert result.connection_limit.value is None


def test_missing_field_across_empty_datapoints_is_unavailable(tmp_path: Path) -> None:
    data = {"service": "empty-service", "window": {}, "db_pool": {}, "datapoints": []}
    metrics_file = tmp_path / "empty.json"
    metrics_file.write_text(json.dumps(data))

    result = extract_cloud_metrics(metrics_file)

    for series in (
        result.database_cpu,
        result.database_connections,
        result.active_connections,
        result.application_cpu,
        result.application_memory,
        result.request_latency,
        result.http_5xx_percentage,
    ):
        assert series.available is False
        assert series.points == []


# --- file handling -------------------------------------------------------


def test_missing_metrics_file_raises_file_not_found(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist.json"

    with pytest.raises(FileNotFoundError):
        extract_cloud_metrics(missing_path)


def test_result_to_dict_is_json_serializable(fixture_metrics_path: Path) -> None:
    result = extract_cloud_metrics(fixture_metrics_path)

    serialized = json.dumps(result.to_dict())
    assert "database_cpu" in serialized
    assert "connection_limit" in serialized


# --- real Phase 3 incident data: known exact peak values ------------------


def test_real_incident_metrics_exact_peak_values() -> None:
    result = extract_cloud_metrics()

    assert result.service == "payment-api"
    assert result.connection_limit.value == 120
    assert max(p.value for p in result.database_cpu.points) == 92
    assert max(p.value for p in result.database_connections.points) == 100.0
    assert max(p.value for p in result.active_connections.points) == 120
    assert max(p.value for p in result.application_cpu.points) == 75
    assert max(p.value for p in result.application_memory.points) == 77
    assert max(p.value for p in result.request_latency.points) == 4300
    assert max(p.value for p in result.http_5xx_percentage.points) == 8.69


def test_real_incident_metrics_baseline_values() -> None:
    result = extract_cloud_metrics()

    assert result.database_cpu.points[0].value == 22
    assert result.database_cpu.points[0].timestamp == "2026-09-12T13:50:00Z"
    assert result.http_5xx_percentage.points[0].value == 0.08


def test_real_incident_data_has_no_db_memory_or_query_latency() -> None:
    result = extract_cloud_metrics()

    assert result.database_memory.available is False
    assert result.query_latency.available is False
