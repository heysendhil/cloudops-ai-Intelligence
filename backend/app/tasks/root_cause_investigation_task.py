"""Root Cause Investigation Task, executed by the Root Cause Investigator
Agent.

Per docs/agent-design.md task #5 (Root Cause Synthesis Task). Takes the
already-produced outputs of the Log Analyst, Cloud Infrastructure Analyst,
Kubernetes Reliability Analyst, and Knowledge/RAG Agent as direct inputs
(embedded verbatim as JSON in the task description -- no Crew/Flow context
wiring is used, since neither is built yet) and defines a strict, exact
output schema. No crew or flow is defined here.
"""

from __future__ import annotations

from crewai import Agent, Task
from pydantic import BaseModel, Field

from app.tasks.cloud_infrastructure_analysis_task import CloudInfrastructureAnalysisReport
from app.tasks.knowledge_retrieval_task import KnowledgeRetrievalReport
from app.tasks.kubernetes_reliability_analysis_task import KubernetesReliabilityReport
from app.tasks.log_analysis_task import LogAnalysisReport

DEFAULT_INCIDENT_ID = "INC-2026-0912"


class EvidenceItem(BaseModel):
    source_agent: str = Field(
        description="Which analyst report this came from: 'Log Analyst', "
        "'Cloud Infrastructure Analyst', 'Kubernetes Reliability Analyst', or "
        "'Knowledge/RAG Agent'."
    )
    fact: str = Field(description="The specific finding being cited, grounded in that report.")
    reference: str = Field(
        description="A specific pointer into the source report (e.g. a raw log line, a "
        "metric name and value, an event, or a runbook excerpt) that this fact came from."
    )


class AlternativeHypothesis(BaseModel):
    hypothesis: str = Field(description="A credible alternative explanation for the incident.")
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="Evidence from the four reports that lends some support to this hypothesis.",
    )
    why_less_likely_than_leading: str = Field(
        description="Concrete, evidence-based explanation of why the leading root_cause is "
        "considered stronger than this alternative."
    )


class RootCauseInvestigationReport(BaseModel):
    root_cause: str = Field(
        description="The single most likely root cause -- the underlying condition that "
        "produced the incident's symptoms, not a restatement of the symptoms themselves."
    )
    evidence: list[EvidenceItem] = Field(default_factory=list)
    alternative_hypotheses: list[AlternativeHypothesis] = Field(default_factory=list)
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Calibrated confidence (0.0-1.0) reflecting the actual strength and "
        "consistency of the evidence across all four reports.",
    )
    missing_evidence: list[str] = Field(
        default_factory=list,
        description="Specific evidence that is not present in the four reports but would "
        "make the conclusion more or less certain if it were available.",
    )


EXPECTED_OUTPUT = (
    "A structured root cause investigation report with exactly these fields: "
    "'root_cause' -- the single most likely underlying root cause, explicitly not a "
    "restatement of symptoms (elevated latency, errors, restarts are symptoms/effects, not "
    "causes); "
    "'evidence' -- every fact supporting the root cause, each with source_agent (which of "
    "the four reports it came from), fact, and reference (a specific pointer into that "
    "report -- a log line, a metric name/value, an event, or a runbook excerpt); "
    "'alternative_hypotheses' -- at least one credible alternative explanation, each with "
    "supporting_evidence and an explicit why_less_likely_than_leading explanation that is "
    "concrete and evidence-based, not dismissive; "
    "'confidence' -- a calibrated number between 0.0 and 1.0 reflecting how strongly and "
    "consistently the evidence across all four reports supports the root_cause -- never a "
    "flat 0.0 or 1.0; and "
    "'missing_evidence' -- specific evidence not present in the four reports that would "
    "strengthen or challenge the conclusion if it were available. "
    "Every fact and reference must be grounded in the four reports provided -- never invent "
    "a metric, log line, event, or runbook excerpt that is not present in them."
)


REQUIREMENTS_TEXT = (
    "Requirements:\n"
    "1. Evidence-based reasoning: every claim must be traceable to one of the four "
    "reports above.\n"
    "2. No invented metrics: never state a number, event, or fact that does not appear "
    "in the reports above.\n"
    "3. Identify alternative hypotheses: name at least one other credible explanation "
    "consistent with at least some of the evidence.\n"
    "4. Explain why the leading hypothesis is stronger: for each alternative, give a "
    "concrete, evidence-based reason it is less likely than your root_cause.\n"
    "5. Explicitly identify missing evidence: name specific evidence not present in the "
    "four reports that would make you more or less certain.\n"
    "6. Calibrate confidence: your confidence must reflect the actual strength and "
    "consistency of the evidence -- do not default to a flat 0.0 or 1.0.\n"
    "7. Do not confuse symptoms with root cause: elevated latency, HTTP errors, and pod "
    "restarts are symptoms/effects; the root_cause must identify the underlying "
    "condition that produced them."
)


def build_root_cause_investigation_task(
    agent: Agent,
    log_analysis: LogAnalysisReport,
    cloud_analysis: CloudInfrastructureAnalysisReport,
    kubernetes_analysis: KubernetesReliabilityReport,
    knowledge_retrieval: KnowledgeRetrievalReport,
    incident_id: str = DEFAULT_INCIDENT_ID,
) -> Task:
    """Build the Root Cause Investigation Task for the given (already-constructed) agent.

    The four analyst reports are embedded verbatim (as JSON) in the task
    description -- this is the agent's only evidence; it has no tool. Use
    this for standalone execution (e.g. testing this task in isolation).
    For Crew execution, see build_root_cause_investigation_task_from_context.
    """
    description = (
        f"Investigate the root cause of incident {incident_id} using only the four analyst "
        "reports below. Do not invent, assume, or add any metric, log line, event, or fact "
        "that is not explicitly present in them.\n\n"
        f"=== Log Analyst report ===\n{log_analysis.model_dump_json(indent=2)}\n\n"
        f"=== Cloud Infrastructure Analyst report ===\n"
        f"{cloud_analysis.model_dump_json(indent=2)}\n\n"
        f"=== Kubernetes Reliability Analyst report ===\n"
        f"{kubernetes_analysis.model_dump_json(indent=2)}\n\n"
        f"=== Knowledge/RAG Agent report ===\n{knowledge_retrieval.model_dump_json(indent=2)}\n\n"
        f"{REQUIREMENTS_TEXT}"
    )

    return Task(
        description=description,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        output_pydantic=RootCauseInvestigationReport,
    )


def build_root_cause_investigation_task_from_context(
    agent: Agent,
    context_tasks: list[Task],
    incident_id: str = DEFAULT_INCIDENT_ID,
) -> Task:
    """Crew-compatible variant of build_root_cause_investigation_task.

    Instead of embedding pre-computed report JSON (which requires the
    upstream tasks to have already run), this relies on CrewAI's native
    `context` mechanism: pass the Log Analysis, Cloud Infrastructure
    Analysis, Kubernetes Reliability Analysis, and Knowledge Retrieval
    Task instances as `context_tasks`, and the Crew engine injects their
    outputs into this task's prompt automatically once they complete.
    """
    description = (
        f"Investigate the root cause of incident {incident_id} using only the evidence "
        "provided in the task context above, from the Log Analyst, Cloud Infrastructure "
        "Analyst, Kubernetes Reliability Analyst, and Knowledge/RAG Agent tasks. Do not "
        "invent, assume, or add any metric, log line, event, or fact that is not explicitly "
        "present in that context.\n\n"
        f"{REQUIREMENTS_TEXT}"
    )

    return Task(
        description=description,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        context=context_tasks,
        output_pydantic=RootCauseInvestigationReport,
    )
