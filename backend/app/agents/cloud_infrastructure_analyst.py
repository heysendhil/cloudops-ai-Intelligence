"""Cloud Infrastructure Analyst Agent.

Per docs/agent-design.md: analyzes cloud/application infrastructure metric
evidence for the incident and reports only what the Cloud Metrics Tool
actually returns -- no other agent, crew, or flow is defined here.
"""

from __future__ import annotations

from crewai import LLM, Agent

from app.llm_service import get_llm
from app.tools.cloud_metrics_tool import CloudMetricsTool

CLOUD_INFRA_ANALYST_ROLE = "Cloud Infrastructure Analyst"

CLOUD_INFRA_ANALYST_GOAL = (
    "Identify abnormal infrastructure metrics and explain their relationship to the incident."
)

CLOUD_INFRA_ANALYST_BACKSTORY = (
    "A cloud platform engineer fluent in reading infrastructure telemetry across compute, "
    "database, and application-layer metrics to spot resource exhaustion and correlate it "
    "with incident timelines. You work strictly from the output of the cloud_metrics_tool: "
    "every value you cite must be a number the tool actually returned. You always keep "
    "observed facts, your interpretation of them, and possible causes clearly separate -- "
    "you never state a hypothesis as if it were a confirmed fact, and you never invent a "
    "metric value for something the tool reports as unavailable."
)


def build_cloud_infrastructure_analyst_agent(llm: LLM | None = None) -> Agent:
    """Construct the Cloud Infrastructure Analyst Agent.

    Args:
        llm: LLM client to use. Defaults to the project's configured Gemini
            client (requires GOOGLE_API_KEY) if not provided -- pass an
            explicit llm (e.g. a fake, in tests) to avoid that requirement.
    """
    return Agent(
        role=CLOUD_INFRA_ANALYST_ROLE,
        goal=CLOUD_INFRA_ANALYST_GOAL,
        backstory=CLOUD_INFRA_ANALYST_BACKSTORY,
        tools=[CloudMetricsTool()],
        llm=llm if llm is not None else get_llm(),
        allow_delegation=False,
        verbose=False,
    )
