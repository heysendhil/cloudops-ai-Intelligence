"""Pure-Python Kubernetes state extraction core for the Kubernetes
Reliability Tool.

No CrewAI, no LLM, and no connection to a real Kubernetes cluster: this
module only reads a simulated cluster-state snapshot from
data/kubernetes/payment-api.json (V1 is simulated/read-only, see
docs/security.md) and extracts the fields that are actually present in it.
Anything not present in the source data is reported as unavailable rather
than estimated or fabricated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_KUBERNETES_PATH = REPO_ROOT / "data" / "kubernetes" / "payment-api.json"


@dataclass(frozen=True)
class ScalarField:
    """A single deployment-level number, or a documented absence."""

    field: str
    unit: str
    available: bool
    value: int | float | None = None
    source_field: str | None = None
    reason_unavailable: str | None = None

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "unit": self.unit,
            "available": self.available,
            "value": self.value,
            "source_field": self.source_field,
            "reason_unavailable": self.reason_unavailable,
        }


@dataclass(frozen=True)
class PodStatus:
    name: str
    phase: str
    ready: bool
    node: str

    def to_dict(self) -> dict:
        return {"name": self.name, "phase": self.phase, "ready": self.ready, "node": self.node}


@dataclass(frozen=True)
class PodRestartCount:
    name: str
    restart_count: int
    restarts: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "restart_count": self.restart_count,
            "restarts": self.restarts,
        }


@dataclass(frozen=True)
class KubernetesEvent:
    time: str
    type: str
    reason: str
    involved_object: str
    source: str
    message: str

    def to_dict(self) -> dict:
        return {
            "time": self.time,
            "type": self.type,
            "reason": self.reason,
            "involved_object": self.involved_object,
            "source": self.source,
            "message": self.message,
        }


@dataclass(frozen=True)
class HealthProbeFinding:
    """Liveness/readiness probe context for one pod: the probe config that
    applies to it (from the Deployment spec) and the actual probe-failure
    events for that specific pod, verbatim from the source events list."""

    pod: str
    restart_triggered: bool
    liveness_probe_config: dict | None
    readiness_probe_config: dict | None
    probe_failure_events: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pod": self.pod,
            "restart_triggered": self.restart_triggered,
            "liveness_probe_config": self.liveness_probe_config,
            "readiness_probe_config": self.readiness_probe_config,
            "probe_failure_events": self.probe_failure_events,
        }


@dataclass(frozen=True)
class KubernetesReliabilityResult:
    source_file: str
    cluster: str
    namespace: str
    snapshot_time: str
    desired_replicas: ScalarField
    ready_replicas: ScalarField
    available_replicas: ScalarField
    pod_status: list[PodStatus]
    pod_restart_counts: list[PodRestartCount]
    events: list[KubernetesEvent]
    health_probe_findings: list[HealthProbeFinding]

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "cluster": self.cluster,
            "namespace": self.namespace,
            "snapshot_time": self.snapshot_time,
            "desired_replicas": self.desired_replicas.to_dict(),
            "ready_replicas": self.ready_replicas.to_dict(),
            "available_replicas": self.available_replicas.to_dict(),
            "pod_status": [p.to_dict() for p in self.pod_status],
            "pod_restart_counts": [p.to_dict() for p in self.pod_restart_counts],
            "events": [e.to_dict() for e in self.events],
            "health_probe_findings": [h.to_dict() for h in self.health_probe_findings],
        }


def _scalar_from_deployment(deployment: dict, field_name: str, unit: str) -> ScalarField:
    if field_name not in deployment:
        return ScalarField(
            field=field_name,
            unit=unit,
            available=False,
            reason_unavailable=f"'{field_name}' is not present in the deployment object.",
        )
    return ScalarField(
        field=field_name,
        unit=unit,
        available=True,
        value=deployment[field_name],
        source_field=f"deployment.{field_name}",
    )


def _ready_replicas(pods: list[dict]) -> ScalarField:
    if not pods:
        return ScalarField(
            field="ready_replicas",
            unit="replicas",
            available=False,
            reason_unavailable="'pods' is not present or empty in the kubernetes state file.",
        )
    ready_count = sum(1 for pod in pods if pod.get("ready") is True)
    return ScalarField(
        field="ready_replicas",
        unit="replicas",
        available=True,
        value=ready_count,
        source_field="computed from pods[].ready",
    )


def extract_kubernetes_reliability(
    k8s_path: Path | str = DEFAULT_KUBERNETES_PATH,
) -> KubernetesReliabilityResult:
    """Read and extract deployment/pod/event facts from a simulated
    Kubernetes state snapshot. Raises FileNotFoundError if the file does not
    exist. Nothing not present in the source data is invented -- deployment
    fields absent from the snapshot are reported as unavailable.
    """
    path = Path(k8s_path)
    if not path.is_file():
        raise FileNotFoundError(f"Kubernetes state file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    deployment = data.get("deployment", {})
    pods = data.get("pods", [])
    events = data.get("events", [])

    pod_status = [
        PodStatus(
            name=pod["name"],
            phase=pod.get("phase", ""),
            ready=pod.get("ready", False),
            node=pod.get("node", ""),
        )
        for pod in pods
        if "name" in pod
    ]

    pod_restart_counts = [
        PodRestartCount(
            name=pod["name"],
            restart_count=pod.get("restart_count", 0),
            restarts=pod.get("restarts", []),
        )
        for pod in pods
        if "name" in pod
    ]

    k8s_events = [
        KubernetesEvent(
            time=event.get("time", ""),
            type=event.get("type", ""),
            reason=event.get("reason", ""),
            involved_object=event.get("involved_object", ""),
            source=event.get("source", ""),
            message=event.get("message", ""),
        )
        for event in events
    ]

    liveness_probe_config = deployment.get("liveness_probe")
    readiness_probe_config = deployment.get("readiness_probe")
    health_probe_findings = [
        HealthProbeFinding(
            pod=pod["name"],
            restart_triggered=pod.get("restart_count", 0) > 0,
            liveness_probe_config=liveness_probe_config,
            readiness_probe_config=readiness_probe_config,
            probe_failure_events=[
                event
                for event in events
                if event.get("involved_object") == f"pod/{pod['name']}"
                and event.get("reason") == "Unhealthy"
            ],
        )
        for pod in pods
        if "name" in pod
    ]

    return KubernetesReliabilityResult(
        source_file=str(path),
        cluster=data.get("cluster", ""),
        namespace=data.get("namespace", ""),
        snapshot_time=data.get("snapshot_time", ""),
        desired_replicas=_scalar_from_deployment(deployment, "desired_replicas", "replicas"),
        ready_replicas=_ready_replicas(pods),
        available_replicas=_scalar_from_deployment(deployment, "available_replicas", "replicas"),
        pod_status=pod_status,
        pod_restart_counts=pod_restart_counts,
        events=k8s_events,
        health_probe_findings=health_probe_findings,
    )
