import json
from pathlib import Path

import pytest
from crewai.tools import BaseTool

from app.tools.kubernetes_reliability_tool import KubernetesReliabilityTool

FIXTURE_K8S = {
    "cluster": "test-cluster",
    "namespace": "test-ns",
    "snapshot_time": "2026-01-01T00:00:00Z",
    "deployment": {
        "name": "test-api",
        "desired_replicas": 3,
        "available_replicas": 2,
        "liveness_probe": {"httpGet": {"path": "/health", "port": 8080}},
        "readiness_probe": {"httpGet": {"path": "/ready", "port": 8080}},
    },
    "pods": [
        {"name": "test-api-1", "node": "node-a", "phase": "Running", "ready": True, "restart_count": 0, "restarts": []},
        {
            "name": "test-api-2",
            "node": "node-b",
            "phase": "Running",
            "ready": True,
            "restart_count": 1,
            "restarts": [{"time": "2026-01-01T00:05:00Z", "reason": "Liveness probe failed", "exit_code": 137}],
        },
    ],
    "events": [
        {
            "time": "2026-01-01T00:04:50Z",
            "type": "Warning",
            "reason": "Unhealthy",
            "involved_object": "pod/test-api-2",
            "source": "kubelet",
            "message": "Liveness probe failed: HTTP probe failed with statuscode: 500",
        }
    ],
}


@pytest.fixture()
def fixture_k8s_path(tmp_path: Path) -> Path:
    k8s_file = tmp_path / "fixture-k8s.json"
    k8s_file.write_text(json.dumps(FIXTURE_K8S))
    return k8s_file


def test_tool_is_a_crewai_basetool() -> None:
    tool = KubernetesReliabilityTool()

    assert isinstance(tool, BaseTool)
    assert tool.name == "kubernetes_reliability_tool"
    assert "kubernetes" in tool.description.lower()


def test_tool_never_claims_a_real_cluster_connection() -> None:
    tool = KubernetesReliabilityTool()

    text = tool.description.lower()
    assert "never connects to a real kubernetes cluster" in text or "simulated" in text


def test_tool_run_returns_all_required_sections(fixture_k8s_path: Path) -> None:
    tool = KubernetesReliabilityTool()

    output = tool.run(k8s_path=str(fixture_k8s_path))

    expected_keys = {
        "desired_replicas",
        "ready_replicas",
        "available_replicas",
        "pod_status",
        "pod_restart_counts",
        "events",
        "health_probe_findings",
    }
    assert expected_keys.issubset(output.keys())


def test_tool_run_extracts_exact_values(fixture_k8s_path: Path) -> None:
    tool = KubernetesReliabilityTool()

    output = tool.run(k8s_path=str(fixture_k8s_path))

    assert output["desired_replicas"]["value"] == 3
    assert output["available_replicas"]["value"] == 2
    assert output["ready_replicas"]["value"] == 2
    assert len(output["pod_status"]) == 2
    assert {p["restart_count"] for p in output["pod_restart_counts"]} == {0, 1}
    assert len(output["events"]) == 1
    assert len(output["health_probe_findings"]) == 2


def test_tool_run_works_without_any_llm_configured(
    fixture_k8s_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    tool = KubernetesReliabilityTool()

    output = tool.run(k8s_path=str(fixture_k8s_path))

    assert output["desired_replicas"]["value"] == 3


def test_tool_default_path_reads_the_real_incident_kubernetes_state() -> None:
    tool = KubernetesReliabilityTool()

    output = tool.run()

    assert output["namespace"] == "payments"
    assert output["desired_replicas"]["value"] == 6
    assert output["ready_replicas"]["value"] == 6
    assert len(output["pod_status"]) == 6
    assert len(output["events"]) == 28
    assert sum(p["restart_count"] for p in output["pod_restart_counts"]) == 4
