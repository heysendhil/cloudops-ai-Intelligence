"""Incident Reporter Agent.

Per docs/agent-design.md: compiles the final incident report from the
incident record and every prior task's output (Log Analyst, Cloud
Infrastructure Analyst, Kubernetes Reliability Analyst, Knowledge/RAG
Agent, Root Cause Investigator, Remediation Advisor). This agent is the
last one in the pipeline -- it compiles, it does not investigate. No Crew
or Flow is defined here.
"""

from __future__ import annotations

from crewai import LLM, Agent

from app.llm_service import get_llm

INCIDENT_REPORTER_ROLE = "Incident Reporter"

INCIDENT_REPORTER_GOAL = (
    "Compile a structured, evidence-grounded final incident report from the incident "
    "record and all prior analyst, root cause, and remediation task outputs -- "
    "introducing no new claims of its own."
)

INCIDENT_REPORTER_BACKSTORY = (
    "A technical writer embedded in the SRE team who turns investigation output into "
    "postmortem-quality documentation. You compile -- you do not investigate. Every fact "
    "in your report (every finding, timestamp, metric, root cause, hypothesis, and "
    "recommendation) must come from the incident record or one of the six prior task "
    "outputs you are given; you never invent evidence, and you never introduce a new "
    "finding, timeline event, or recommendation that isn't already present in them. When "
    "compiling the timeline, you cite which prior report each event came from. When "
    "compiling remediation recommendations, you carry them through exactly as given -- you "
    "never alter, add, or drop one -- and you always restate that every recommendation "
    "requires human approval, since this system never executes remediation on its own."
)


def build_incident_reporter_agent(llm: LLM | None = None) -> Agent:
    """Construct the Incident Reporter Agent.

    Args:
        llm: LLM client to use. Defaults to the project's configured Gemini
            client (requires GOOGLE_API_KEY) if not provided -- pass an
            explicit llm (e.g. a fake, in tests) to avoid that requirement.
    """
    return Agent(
        role=INCIDENT_REPORTER_ROLE,
        goal=INCIDENT_REPORTER_GOAL,
        backstory=INCIDENT_REPORTER_BACKSTORY,
        tools=[],
        llm=llm if llm is not None else get_llm(),
        allow_delegation=False,
        verbose=False,
    )
