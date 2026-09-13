"""CrewAI-compatible wrapper around the kubernetes_parser core.

This module only adapts extract_kubernetes_reliability to CrewAI's BaseTool
contract (name, description, args_schema, _run). All extraction logic lives
in kubernetes_parser.py, which never connects to a real Kubernetes cluster --
V1 is simulated/read-only (see docs/security.md). This tool is not wired to
any Agent, Crew, or Flow yet.
"""

from __future__ import annotations

from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.tools.kubernetes_parser import DEFAULT_KUBERNETES_PATH, extract_kubernetes_reliability


class KubernetesReliabilityToolInput(BaseModel):
    k8s_path: str | None = Field(
        default=None,
        description="Path to the Kubernetes state JSON file to read. Defaults to data/kubernetes/payment-api.json.",
    )


class KubernetesReliabilityTool(BaseTool):
    """Reads a simulated Kubernetes cluster-state snapshot and extracts
    deployment replica counts, pod status, pod restart counts, Kubernetes
    events, and health probe findings. Never connects to a real cluster --
    V1 is simulated and read-only. Uses no LLM. Anything not present in the
    source file is reported as unavailable, never invented.
    """

    name: str = "kubernetes_reliability_tool"
    description: str = (
        "Reads a simulated Kubernetes state JSON file and extracts deployment desired/ready/"
        "available replica counts, per-pod status, per-pod restart counts, the raw Kubernetes "
        "events, and health probe findings (liveness/readiness probe config plus the actual "
        "probe-failure events for each pod). This tool never connects to a real Kubernetes "
        "cluster -- it only reads simulated, checked-in state (V1 is read-only). A field not "
        "present in the source file is reported as unavailable rather than invented."
    )
    args_schema: type[BaseModel] = KubernetesReliabilityToolInput

    def _run(self, k8s_path: str | None = None) -> dict:
        result = extract_kubernetes_reliability(
            Path(k8s_path) if k8s_path else DEFAULT_KUBERNETES_PATH
        )
        return result.to_dict()
