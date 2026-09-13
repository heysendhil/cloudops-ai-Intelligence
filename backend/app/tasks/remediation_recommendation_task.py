"""Remediation Recommendation Task, executed by the Remediation Advisor
Agent.

Per docs/agent-design.md task #6 (Remediation Recommendation Task). Takes
the already-produced Root Cause Investigation report and Knowledge
Retrieval (runbook) report as direct inputs (embedded verbatim as JSON in
the task description -- no Crew/Flow context wiring, since neither is
built yet). Every recommendation's requires_human_approval is typed as
Literal[True]: the schema itself makes it impossible for the model to
produce a recommendation that doesn't require human approval -- a
validation error, not silent wrong data, is what a False value produces.
No crew or flow is defined here.
"""

from __future__ import annotations

from typing import Literal

from crewai import Agent, Task
from pydantic import BaseModel, Field

from app.tasks.knowledge_retrieval_task import KnowledgeRetrievalReport
from app.tasks.root_cause_investigation_task import RootCauseInvestigationReport

DEFAULT_INCIDENT_ID = "INC-2026-0912"


class Recommendation(BaseModel):
    action: str = Field(description="The specific recommended action.")
    reason: str = Field(
        description="Why this action is recommended, grounded in the RCA and/or runbook."
    )
    risk: str = Field(
        description="Honest risk assessment for this action (e.g. level and rationale -- "
        "reversibility, blast radius, likelihood of making things worse)."
    )
    requires_human_approval: Literal[True] = Field(
        description="Always true -- this system never executes remediation; every "
        "recommendation requires a human to review and approve it before any action is taken."
    )


class RemediationRecommendationReport(BaseModel):
    recommendations: list[Recommendation] = Field(default_factory=list)
    safety_notice: str = Field(
        description="Explicit statement that this system is advisory only, never executes "
        "any change, and every recommendation above requires human approval."
    )
    summary: str = Field(description="Short prose summary of the recommended approach.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence (0.0-1.0) that these recommendations address the root cause.",
    )


EXPECTED_OUTPUT = (
    "A structured remediation recommendation report with exactly these fields: "
    "'recommendations' -- a list of recommendations, each with exactly 'action' (the "
    "specific recommended action), 'reason' (why, grounded in the RCA and/or runbook), "
    "'risk' (an honest risk assessment), and 'requires_human_approval' (always true -- "
    "this system never executes remediation); "
    "'safety_notice' -- an explicit statement that this system is advisory only and every "
    "recommendation requires human approval before any action is taken; "
    "'summary' -- a short prose summary of the recommended approach; and "
    "'confidence' -- a number between 0.0 and 1.0 reflecting how confident you are that "
    "these recommendations address the root cause. "
    "Every recommendation's reason must be traceable to the root cause investigation's "
    "evidence or the runbook knowledge provided -- never invent a cause, fact, or procedure "
    "not present in them. Never phrase a recommendation as something you have already done, "
    "are doing, or will do yourself -- you only recommend; a human decides and acts."
)

REQUIREMENTS_TEXT = (
    "Requirements:\n"
    "1. Recommendation quality: propose concrete, specific, actionable recommendations "
    "-- not vague platitudes -- appropriate to the root cause and any relevant "
    "alternative hypotheses above.\n"
    "2. Safety: you must NEVER execute, apply, or claim to have already performed any "
    "production change. You are only recommending; you have no ability to act on any "
    "system. Every recommendation's requires_human_approval must be true.\n"
    "3. Evidence grounding: every recommendation's reason must be traceable to specific "
    "evidence in the root cause investigation (root_cause, evidence, "
    "alternative_hypotheses) and/or the runbook report (retrieved_knowledge, "
    "troubleshooting_procedures) above -- never invent a cause, fact, or procedure not "
    "present in them.\n"
    "4. Approval requirement: state explicitly, both per-recommendation and in the "
    "overall safety_notice, that all production changes require human approval -- this "
    "system does not and cannot execute remediation on its own."
)


def build_remediation_recommendation_task(
    agent: Agent,
    rca: RootCauseInvestigationReport,
    knowledge: KnowledgeRetrievalReport,
    incident_id: str = DEFAULT_INCIDENT_ID,
) -> Task:
    """Build the Remediation Recommendation Task for the given (already-constructed) agent.

    Use this for standalone execution (e.g. testing this task in
    isolation). For Crew execution, see
    build_remediation_recommendation_task_from_context.
    """
    description = (
        f"Recommend remediation options for incident {incident_id} based only on the root "
        "cause investigation and runbook knowledge below.\n\n"
        f"=== Root Cause Investigation report ===\n{rca.model_dump_json(indent=2)}\n\n"
        f"=== Knowledge/RAG (runbook) report ===\n{knowledge.model_dump_json(indent=2)}\n\n"
        f"{REQUIREMENTS_TEXT}"
    )

    return Task(
        description=description,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        output_pydantic=RemediationRecommendationReport,
    )


def build_remediation_recommendation_task_from_context(
    agent: Agent,
    context_tasks: list[Task],
    incident_id: str = DEFAULT_INCIDENT_ID,
) -> Task:
    """Crew-compatible variant of build_remediation_recommendation_task.

    Instead of embedding pre-computed report JSON (which requires the
    upstream tasks to have already run), this relies on CrewAI's native
    `context` mechanism: pass the Root Cause Investigation and Knowledge
    Retrieval Task instances as `context_tasks`, and the Crew engine
    injects their outputs into this task's prompt automatically once they
    complete.
    """
    description = (
        f"Recommend remediation options for incident {incident_id} based only on the root "
        "cause investigation and runbook knowledge provided in the task context above.\n\n"
        f"{REQUIREMENTS_TEXT}"
    )

    return Task(
        description=description,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        context=context_tasks,
        output_pydantic=RemediationRecommendationReport,
    )
