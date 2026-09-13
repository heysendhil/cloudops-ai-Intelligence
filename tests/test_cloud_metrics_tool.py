import json
from pathlib import Path

import pytest
from crewai.tools import BaseTool

from app.tools.cloud_metrics_tool import CloudMetricsTool

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
        }
    ],
}


@pytest.fixture()
def fixture_metrics_path(tmp_path: Path) -> Path:
    metrics_file = tmp_path / "fixture-metrics.json"
    metrics_file.write_text(json.dumps(FIXTURE_METRICS))
    return metrics_file


def test_tool_is_a_crewai_basetool() -> None:
    tool = CloudMetricsTool()

    assert isinstance(tool, BaseTool)
    assert tool.name == "cloud_metrics_tool"
    assert "metrics" in tool.description.lower()


def test_tool_run_returns_all_ten_requested_metrics(fixture_metrics_path: Path) -> None:
    tool = CloudMetricsTool()

    output = tool.run(metrics_path=str(fixture_metrics_path))

    expected_keys = {
        "database_cpu",
        "database_memory",
        "database_connections",
        "connection_limit",
        "active_connections",
        "query_latency",
        "application_cpu",
        "application_memory",
        "request_latency",
        "http_5xx_percentage",
    }
    assert expected_keys.issubset(output.keys())


def test_tool_run_extracts_exact_values(fixture_metrics_path: Path) -> None:
    tool = CloudMetricsTool()

    output = tool.run(metrics_path=str(fixture_metrics_path))

    assert output["database_cpu"]["points"][0]["value"] == 20
    assert output["connection_limit"]["value"] == 50
    assert output["active_connections"]["points"][0]["value"] == 8
    assert output["http_5xx_percentage"]["points"][0]["value"] == 1.0


def test_tool_run_never_invents_missing_metrics(fixture_metrics_path: Path) -> None:
    tool = CloudMetricsTool()

    output = tool.run(metrics_path=str(fixture_metrics_path))

    assert output["database_memory"]["available"] is False
    assert output["database_memory"]["points"] == []
    assert output["query_latency"]["available"] is False
    assert output["query_latency"]["points"] == []


def test_tool_run_works_without_any_llm_configured(
    fixture_metrics_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    tool = CloudMetricsTool()

    output = tool.run(metrics_path=str(fixture_metrics_path))

    assert output["database_cpu"]["points"][0]["value"] == 20


def test_tool_default_path_reads_the_real_incident_metrics() -> None:
    tool = CloudMetricsTool()

    output = tool.run()

    assert output["service"] == "payment-api"
    assert output["connection_limit"]["value"] == 120
    assert max(p["value"] for p in output["database_cpu"]["points"]) == 92
    assert max(p["value"] for p in output["http_5xx_percentage"]["points"]) == 8.69
    assert output["database_memory"]["available"] is False
    assert output["query_latency"]["available"] is False
