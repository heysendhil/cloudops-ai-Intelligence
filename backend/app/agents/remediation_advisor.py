"""Remediation Advisor Agent.

Per docs/agent-design.md: proposes remediation options grounded in the Root
Cause Investigator's findings and runbook knowledge. This agent is
advisory only -- it has no tool that can act on any infrastructure, and
every recommendation it produces requires human approval (see CLAUDE.md's
V1 constraint: no automatic remediation execution). No Crew or Incident
Reporter agent is defined here.
"""

from __future__ import annotations

from crewai import LLM, Agent

from app.llm_service import get_llm

REMEDIATION_ADVISOR_ROLE = "Remediation Advisor"

REMEDIATION_ADVISOR_GOAL = (
    "Generate safe, evidence-grounded remediation recommendations based on the root cause "
    "investigation and relevant runbook guidance -- never executing any change, and always "
    "requiring human approval before any recommendation is acted on."
)

REMEDIATION_ADVISOR_BACKSTORY = (
    "A senior SRE who has resolved this class of incident before and knows the trade-offs "
    "between a quick mitigation and a durable fix. You propose remediation options for a "
    "human responder to evaluate -- you never execute, apply, or claim to have already "
    "performed any change against production or any other system; this project's V1 is "
    "read-only and does not perform automated remediation (see CLAUDE.md, "
    "docs/security.md). Every recommendation you produce always requires human approval, "
    "without exception. You ground every recommendation in the root cause investigation's "
    "evidence and/or the retrieved runbook knowledge you are given -- you never invent a "
    "cause, fact, or procedure that isn't present in them. You state each recommendation's "
    "risk honestly, including when a recommendation is high-risk or only partially "
    "addresses the root cause, rather than making every option sound safe and effective."
)


def build_remediation_advisor_agent(llm: LLM | None = None) -> Agent:
    """Construct the Remediation Advisor Agent.

    Args:
        llm: LLM client to use. Defaults to the project's configured Gemini
            client (requires GOOGLE_API_KEY) if not provided -- pass an
            explicit llm (e.g. a fake, in tests) to avoid that requirement.
    """
    return Agent(
        role=REMEDIATION_ADVISOR_ROLE,
        goal=REMEDIATION_ADVISOR_GOAL,
        backstory=REMEDIATION_ADVISOR_BACKSTORY,
        tools=[],
        llm=llm if llm is not None else get_llm(),
        allow_delegation=False,
        verbose=False,
    )
