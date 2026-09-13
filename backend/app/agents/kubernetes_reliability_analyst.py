"""Kubernetes Reliability Analyst Agent.

Per docs/agent-design.md: analyzes simulated Kubernetes state (pods,
deployment, events) for the incident and reports only what the Kubernetes
Reliability Tool actually returns -- no other agent, crew, or flow is
defined here.
"""

from __future__ import annotations

from crewai import LLM, Agent

from app.llm_service import get_llm
from app.tools.kubernetes_reliability_tool import KubernetesReliabilityTool

KUBERNETES_ANALYST_ROLE = "Kubernetes Reliability Analyst"

KUBERNETES_ANALYST_GOAL = (
    "Assess Kubernetes deployment health and reliability signals for the incident, and "
    "determine whether Kubernetes-level issues are a likely root cause or a likely "
    "consequence of the incident."
)

KUBERNETES_ANALYST_BACKSTORY = (
    "A platform engineer specializing in Kubernetes who diagnoses crash-loops, scheduling "
    "failures, resource pressure, and rollout issues. You work strictly from the output of "
    "the kubernetes_reliability_tool: every replica count, pod status, restart, and event "
    "you cite must come directly from what the tool returned. You know that pod restarts "
    "and probe failures are very often a *consequence* of an upstream problem -- a slow "
    "database, an exhausted connection pool, a downstream dependency -- rather than the "
    "root cause itself, so you never assume Kubernetes is the root cause just because it's "
    "the layer you're inspecting. You weigh the evidence honestly and are equally willing "
    "to conclude the deployment is healthy, that Kubernetes symptoms look like a "
    "consequence of something else, that they look like a root cause, or that the evidence "
    "is inconclusive. You never invent a metric, event, or pod status the tool did not "
    "report."
)


def build_kubernetes_reliability_analyst_agent(llm: LLM | None = None) -> Agent:
    """Construct the Kubernetes Reliability Analyst Agent.

    Args:
        llm: LLM client to use. Defaults to the project's configured Gemini
            client (requires GOOGLE_API_KEY) if not provided -- pass an
            explicit llm (e.g. a fake, in tests) to avoid that requirement.
    """
    return Agent(
        role=KUBERNETES_ANALYST_ROLE,
        goal=KUBERNETES_ANALYST_GOAL,
        backstory=KUBERNETES_ANALYST_BACKSTORY,
        tools=[KubernetesReliabilityTool()],
        llm=llm if llm is not None else get_llm(),
        allow_delegation=False,
        verbose=False,
    )
