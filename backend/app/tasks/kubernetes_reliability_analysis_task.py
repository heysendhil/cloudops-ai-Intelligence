"""Kubernetes Reliability Analysis Task, executed by the Kubernetes
Reliability Analyst Agent.

Per docs/agent-design.md task #3 (Kubernetes Reliability Analysis Task).
Defines a strict, structured expected output that forces an explicit
root-cause-vs-consequence judgment (never defaulted to "root cause") and
grounds every finding in the kubernetes_reliability_tool's actual output --
no crew or flow is defined here.
"""

from __future__ import annotations

from typing import Literal

from crewai import Agent, Task
from pydantic import BaseModel, Field

from app.tools.kubernetes_reliability_tool import KubernetesReliabilityTool

DEFAULT_INCIDENT_ID = "INC-2026-0912"

RootCauseAssessment = Literal["likely_root_cause", "likely_consequence", "inconclusive"]


class PodRestartPatternFinding(BaseModel):
    pod: str = Field(description="Pod name.")
    restart_count: int = Field(description="Restart count for this pod, from the tool.")
    pattern_description: str = Field(
        description="Description of the restart pattern for this pod, grounded in the "
        "tool's restarts/events data (e.g. timing relative to probe failures)."
    )


class ProbeFailureFinding(BaseModel):
    pod: str = Field(description="Pod name.")
    probe_type: str = Field(description="Which probe failed, e.g. liveness or readiness.")
    failure_count: int = Field(
        description="Number of probe-failure events for this pod, from the tool."
    )
    description: str = Field(description="What the probe failures show for this pod.")


class CitedKubernetesEvent(BaseModel):
    time: str = Field(description="Event timestamp, verbatim from the tool.")
    type: str = Field(description="Event type, e.g. Warning or Normal, verbatim from the tool.")
    reason: str = Field(description="Event reason, verbatim from the tool.")
    involved_object: str = Field(description="Involved object, verbatim from the tool.")
    message: str = Field(description="Event message, verbatim from the tool.")


class KubernetesReliabilityReport(BaseModel):
    deployment_healthy: bool = Field(
        description="Whether the deployment is currently healthy, based on desired/ready/"
        "available replica counts from the tool."
    )
    deployment_health_explanation: str = Field(
        description="Explanation grounded in the tool's replica counts and pod statuses."
    )
    pod_restart_patterns: list[PodRestartPatternFinding] = Field(default_factory=list)
    probe_failures: list[ProbeFailureFinding] = Field(default_factory=list)
    relevant_events: list[CitedKubernetesEvent] = Field(default_factory=list)
    root_cause_assessment: RootCauseAssessment = Field(
        description="Whether Kubernetes-level issues look like a likely root cause, a "
        "likely consequence of an upstream issue, or the evidence is inconclusive. Must "
        "never default to 'likely_root_cause' without evidence that specifically supports it."
    )
    root_cause_reasoning: str = Field(
        description="Reasoning for the root_cause_assessment, explicitly weighing both "
        "possibilities (root cause vs. consequence) against the evidence."
    )
    summary: str = Field(description="Short prose summary of the Kubernetes reliability evidence.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence (0.0-1.0) that the Kubernetes evidence alone supports the summary.",
    )


EXPECTED_OUTPUT = (
    "A structured Kubernetes reliability report with exactly these fields: "
    "'deployment_healthy' -- true/false, based on the tool's desired/ready/available "
    "replica counts and pod statuses; "
    "'deployment_health_explanation' -- grounded explanation for that determination; "
    "'pod_restart_patterns' -- for each pod with restarts, its restart_count and a "
    "description of the restart pattern (e.g. timing relative to probe failures), grounded "
    "in the tool's pod_restart_counts data; "
    "'probe_failures' -- for each pod with probe failures, which probe failed, how many "
    "times, and what it shows, grounded in the tool's health_probe_findings; "
    "'relevant_events' -- the specific Kubernetes events (verbatim time/type/reason/"
    "involved_object/message) that support the analysis; "
    "'root_cause_assessment' -- exactly one of 'likely_root_cause', 'likely_consequence', "
    "or 'inconclusive', reflecting whether Kubernetes-level issues appear to be the root "
    "cause of the incident or a consequence of an upstream problem (e.g. a database issue) "
    "-- this must never default to 'likely_root_cause' without evidence that specifically "
    "supports it, since pod restarts and probe failures are frequently downstream symptoms; "
    "'root_cause_reasoning' -- reasoning that explicitly weighs both possibilities against "
    "the evidence; "
    "'summary' -- a short prose summary; and "
    "'confidence' -- a number between 0.0 and 1.0. "
    "Every fact cited (replica counts, pod names, restart counts, events) must be traceable "
    "to what the kubernetes_reliability_tool actually returned -- never invent a pod, "
    "event, or count."
)


def build_kubernetes_reliability_analysis_task(
    agent: Agent,
    k8s_path: str | None = None,
    incident_id: str = DEFAULT_INCIDENT_ID,
) -> Task:
    """Build the Kubernetes Reliability Analysis Task for the given (already-constructed) agent."""
    tool_call_instruction = (
        f"Call the kubernetes_reliability_tool with k8s_path='{k8s_path}'"
        if k8s_path
        else "Call the kubernetes_reliability_tool with no arguments (it will read the default Kubernetes state file)"
    )

    description = (
        f"Investigate incident {incident_id} by analyzing its Kubernetes reliability "
        f"evidence. {tool_call_instruction} to read the deployment's desired/ready/available "
        "replica counts, per-pod status, per-pod restart counts, Kubernetes events, and "
        "health probe findings. Determine whether the deployment is healthy, describe the "
        "pod restart patterns and probe failures, and cite the relevant Kubernetes events. "
        "Then explicitly assess whether Kubernetes-level issues look like a likely root "
        "cause of the incident, a likely consequence of an upstream problem, or the "
        "evidence is inconclusive -- do not assume Kubernetes is the root cause just "
        "because you are analyzing Kubernetes evidence; pod restarts and probe failures "
        "are often a downstream symptom of something else (e.g. a database or dependency "
        "issue), so weigh both possibilities against the evidence before deciding. Do not "
        "invent a pod, event, replica count, or restart that the tool did not return, and "
        "if a value is reported as unavailable, say so rather than guessing."
    )

    return Task(
        description=description,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        tools=[KubernetesReliabilityTool()],
        output_pydantic=KubernetesReliabilityReport,
    )
