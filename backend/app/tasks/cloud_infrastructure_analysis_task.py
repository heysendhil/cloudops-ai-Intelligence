"""Cloud Infrastructure Analysis Task, executed by the Cloud Infrastructure
Analyst Agent.

Per docs/agent-design.md task #2 (Cloud Infrastructure Analysis Task).
Defines a strict, structured expected output that keeps observed facts,
interpretation, and possible causes clearly separate, and instructs the
agent to ground every fact in the cloud_metrics_tool's actual output -- no
crew or flow is defined here.
"""

from __future__ import annotations

from crewai import Agent, Task
from pydantic import BaseModel, Field

from app.tools.cloud_metrics_tool import CloudMetricsTool

DEFAULT_INCIDENT_ID = "INC-2026-0912"


class ObservedMetricFact(BaseModel):
    metric: str = Field(description="Metric name, e.g. database_cpu.")
    value: float = Field(description="The exact value returned by the cloud_metrics_tool.")
    unit: str = Field(description="Unit of the value, e.g. percent, ms, connections.")
    timestamp: str = Field(description="ISO 8601 timestamp the value was observed at.")
    source_field: str = Field(description="The tool's source_field this value came from.")
    relationship_to_incident: str = Field(
        description="Why this observation is abnormal and how it relates to the incident timeline."
    )


class CloudInfrastructureAnalysisReport(BaseModel):
    observed_facts: list[ObservedMetricFact] = Field(default_factory=list)
    interpretation: str = Field(
        description="Prose reasoning about what the observed facts suggest together -- "
        "clearly framed as interpretation, not as additional fact."
    )
    possible_causes: list[str] = Field(
        default_factory=list,
        description="Hedged, plausible root-cause hypotheses consistent with the observed "
        "facts -- explicitly not a confirmed conclusion.",
    )
    summary: str = Field(description="Short prose summary of the infrastructure evidence.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence (0.0-1.0) that the metric evidence alone supports the summary.",
    )


EXPECTED_OUTPUT = (
    "A structured cloud infrastructure analysis report with exactly these fields: "
    "'observed_facts' -- every abnormal or notable metric actually returned by the "
    "cloud_metrics_tool, each with metric name, value, unit, timestamp, the tool's "
    "source_field, and a relationship_to_incident explanation of why it matters; "
    "'interpretation' -- prose reasoning about what the observed facts suggest together, "
    "clearly framed as interpretation and never presented as an additional fact; "
    "'possible_causes' -- a list of hedged, plausible root-cause hypotheses consistent with "
    "the observed facts, explicitly not a confirmed conclusion; "
    "'summary' -- a short prose summary of the infrastructure evidence; and "
    "'confidence' -- a number between 0.0 and 1.0 reflecting how strongly the metric "
    "evidence alone supports the summary. "
    "Every observed fact must be traceable to a value the cloud_metrics_tool actually "
    "returned. Never invent a metric or a value, and if the tool reports a metric as "
    "unavailable, say so rather than guessing a plausible number."
)


def build_cloud_infrastructure_analysis_task(
    agent: Agent,
    metrics_path: str | None = None,
    incident_id: str = DEFAULT_INCIDENT_ID,
) -> Task:
    """Build the Cloud Infrastructure Analysis Task for the given (already-constructed) agent."""
    tool_call_instruction = (
        f"Call the cloud_metrics_tool with metrics_path='{metrics_path}'"
        if metrics_path
        else "Call the cloud_metrics_tool with no arguments (it will read the default metrics file)"
    )

    description = (
        f"Investigate incident {incident_id} by analyzing its cloud/application infrastructure "
        f"metrics. {tool_call_instruction} to read database CPU, database memory, database "
        "connections, connection limit, active connections, query latency, application CPU, "
        "application memory, request latency, and HTTP 5xx percentage. Identify which of these "
        "metrics are abnormal (e.g. saturated, far above baseline, or missing) and explain how "
        "each relates to the incident timeline. Keep three things clearly separate: observed "
        "facts (only the exact values the tool returned), your interpretation (what those facts "
        "suggest when read together), and possible causes (explicitly hedged hypotheses, not "
        "confirmed conclusions). Do not invent a metric or a metric value the tool did not "
        "return, and if a metric is reported as unavailable, say so rather than guessing a "
        "plausible number."
    )

    return Task(
        description=description,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        tools=[CloudMetricsTool()],
        output_pydantic=CloudInfrastructureAnalysisReport,
    )
