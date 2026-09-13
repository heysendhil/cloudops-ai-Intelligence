"""Incident Reporting Task, executed by the Incident Reporter Agent.

Per docs/agent-design.md task #7 (Incident Report Compilation Task). Takes
the incident record's core metadata plus all six prior task outputs (Log
Analyst, Cloud Infrastructure Analyst, Kubernetes Reliability Analyst,
Knowledge/RAG Agent, Root Cause Investigator, Remediation Advisor) as
direct inputs, embedded verbatim as JSON in the task description -- no
Crew/Flow context wiring, since neither is built yet. Defines a structured
output with exactly the 14 required report sections. No crew or flow is
defined here.
"""

from __future__ import annotations

from crewai import Agent, Task
from pydantic import BaseModel, Field

from app.tasks.cloud_infrastructure_analysis_task import CloudInfrastructureAnalysisReport
from app.tasks.knowledge_retrieval_task import KnowledgeRetrievalReport
from app.tasks.kubernetes_reliability_analysis_task import KubernetesReliabilityReport
from app.tasks.log_analysis_task import LogAnalysisReport
from app.tasks.remediation_recommendation_task import Recommendation, RemediationRecommendationReport
from app.tasks.root_cause_investigation_task import RootCauseInvestigationReport

DEFAULT_INCIDENT_ID = "INC-2026-0912"
DEFAULT_SEVERITY = "SEV-2"
DEFAULT_SERVICE = "Payment API"
DEFAULT_IMPACT = (
    "Checkout and payment confirmation requests experienced elevated latency and "
    "intermittent failures; some payment attempts returned HTTP 500 and required client "
    "retry."
)


class TimelineEntry(BaseModel):
    timestamp: str = Field(description="ISO 8601 timestamp, taken from one of the six reports.")
    description: str = Field(description="What happened at this point in the incident.")
    source: str = Field(
        description="Which prior report this timeline entry came from, e.g. 'Log Analyst' "
        "or 'Kubernetes Reliability Analyst'."
    )


class IncidentReport(BaseModel):
    incident_id: str = Field(description="The incident identifier, exactly as given.")
    severity: str = Field(description="The incident severity, exactly as given.")
    service: str = Field(description="The affected service, exactly as given.")
    impact: str = Field(description="The incident's impact, exactly as given.")
    timeline: list[TimelineEntry] = Field(default_factory=list)
    log_findings: str = Field(
        description="Summary of the Log Analyst's findings, grounded in that report."
    )
    cloud_findings: str = Field(
        description="Summary of the Cloud Infrastructure Analyst's findings, grounded in "
        "that report."
    )
    kubernetes_findings: str = Field(
        description="Summary of the Kubernetes Reliability Analyst's findings, grounded in "
        "that report."
    )
    relevant_runbook: str = Field(
        description="Summary of the relevant runbook knowledge retrieved, grounded in the "
        "Knowledge/RAG Agent's report."
    )
    root_cause: str = Field(description="The root cause, exactly as given by the Root Cause "
        "Investigator.")
    alternative_hypotheses: list[str] = Field(
        default_factory=list,
        description="The alternative hypotheses considered, grounded in the Root Cause "
        "Investigator's report.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="The Root Cause Investigator's confidence, carried through unchanged.",
    )
    remediation_recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="The Remediation Advisor's recommendations, carried through exactly as "
        "given -- never altered, added to, or dropped.",
    )
    human_approval_requirement: str = Field(
        description="Explicit statement that every remediation recommendation above "
        "requires human approval before any action is taken -- this system never executes "
        "remediation automatically."
    )


EXPECTED_OUTPUT = (
    "A structured final incident report with exactly these fields: 'incident_id', "
    "'severity', 'service', and 'impact' (copied exactly from the incident record given); "
    "'timeline' (events with timestamp, description, and source, drawn only from "
    "timestamps/events actually present in the six reports below); 'log_findings', "
    "'cloud_findings', 'kubernetes_findings' (summaries grounded in the respective "
    "analyst's report); 'relevant_runbook' (summary grounded in the Knowledge/RAG Agent's "
    "report); 'root_cause', 'alternative_hypotheses', and 'confidence' (carried through "
    "from the Root Cause Investigator's report); 'remediation_recommendations' (carried "
    "through exactly from the Remediation Advisor's report, unaltered); and "
    "'human_approval_requirement' (an explicit statement that every recommendation "
    "requires human approval). The reporter must only use information supplied by the "
    "incident record and the six prior task outputs below -- it must not invent evidence, "
    "a finding, a timestamp, or a recommendation not already present in them."
)


INSTRUCTIONS_TEXT = (
    "Instructions:\n"
    "1. Copy incident_id, severity, service, and impact exactly as given above.\n"
    "2. Build the timeline only from timestamps/events actually present in the reports "
    "above (log timestamps, cloud metric timestamps, Kubernetes event times), citing "
    "which report each entry came from.\n"
    "3. Summarize log_findings, cloud_findings, and kubernetes_findings strictly from "
    "the corresponding report above -- do not add a finding that report did not make.\n"
    "4. Summarize relevant_runbook strictly from the Knowledge/RAG Agent report above.\n"
    "5. Carry root_cause, alternative_hypotheses, and confidence through from the Root "
    "Cause Investigator report above, unchanged in substance.\n"
    "6. Carry remediation_recommendations through exactly from the Remediation Advisor "
    "report above -- do not alter, add, or drop any recommendation.\n"
    "7. State human_approval_requirement explicitly: every recommendation above "
    "requires human approval; this system never executes remediation automatically."
)


def build_incident_reporting_task(
    agent: Agent,
    log_analysis: LogAnalysisReport,
    cloud_analysis: CloudInfrastructureAnalysisReport,
    kubernetes_analysis: KubernetesReliabilityReport,
    knowledge_retrieval: KnowledgeRetrievalReport,
    rca: RootCauseInvestigationReport,
    remediation: RemediationRecommendationReport,
    incident_id: str = DEFAULT_INCIDENT_ID,
    severity: str = DEFAULT_SEVERITY,
    service: str = DEFAULT_SERVICE,
    impact: str = DEFAULT_IMPACT,
) -> Task:
    """Build the Incident Reporting Task for the given (already-constructed) agent.

    Use this for standalone execution (e.g. testing this task in
    isolation). For Crew execution, see build_incident_reporting_task_from_context.
    """
    description = (
        "Compile the final incident report using only the incident record below and the "
        "six prior task outputs below. Do not invent any evidence, finding, timestamp, or "
        "recommendation that is not already present in them.\n\n"
        f"=== Incident record ===\n"
        f"incident_id: {incident_id}\nseverity: {severity}\nservice: {service}\n"
        f"impact: {impact}\n\n"
        f"=== Log Analyst report ===\n{log_analysis.model_dump_json(indent=2)}\n\n"
        f"=== Cloud Infrastructure Analyst report ===\n"
        f"{cloud_analysis.model_dump_json(indent=2)}\n\n"
        f"=== Kubernetes Reliability Analyst report ===\n"
        f"{kubernetes_analysis.model_dump_json(indent=2)}\n\n"
        f"=== Knowledge/RAG Agent report ===\n{knowledge_retrieval.model_dump_json(indent=2)}\n\n"
        f"=== Root Cause Investigator report ===\n{rca.model_dump_json(indent=2)}\n\n"
        f"=== Remediation Advisor report ===\n{remediation.model_dump_json(indent=2)}\n\n"
        f"{INSTRUCTIONS_TEXT}"
    )

    return Task(
        description=description,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        output_pydantic=IncidentReport,
    )


def build_incident_reporting_task_from_context(
    agent: Agent,
    context_tasks: list[Task],
    incident_id: str = DEFAULT_INCIDENT_ID,
    severity: str = DEFAULT_SEVERITY,
    service: str = DEFAULT_SERVICE,
    impact: str = DEFAULT_IMPACT,
) -> Task:
    """Crew-compatible variant of build_incident_reporting_task.

    Instead of embedding pre-computed report JSON (which requires all six
    upstream tasks to have already run), this relies on CrewAI's native
    `context` mechanism: pass the Log Analysis, Cloud Infrastructure
    Analysis, Kubernetes Reliability Analysis, Knowledge Retrieval, Root
    Cause Investigation, and Remediation Recommendation Task instances as
    `context_tasks`, and the Crew engine injects their outputs into this
    task's prompt automatically once they complete. incident_id, severity,
    service, and impact are plain incident-record data, not an agent
    output, so they're still passed directly and embedded verbatim.
    """
    description = (
        "Compile the final incident report using only the incident record below and the "
        "six prior task outputs provided in the task context above. Do not invent any "
        "evidence, finding, timestamp, or recommendation that is not already present in "
        "them.\n\n"
        f"=== Incident record ===\n"
        f"incident_id: {incident_id}\nseverity: {severity}\nservice: {service}\n"
        f"impact: {impact}\n\n"
        f"{INSTRUCTIONS_TEXT}"
    )

    return Task(
        description=description,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        context=context_tasks,
        output_pydantic=IncidentReport,
    )
