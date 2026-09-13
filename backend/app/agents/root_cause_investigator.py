"""Root Cause Investigator Agent.

Per docs/agent-design.md: synthesizes the Log Analyst, Cloud Infrastructure
Analyst, Kubernetes Reliability Analyst, and Knowledge/RAG Agent outputs
into ranked root-cause hypotheses. No tool beyond the LLM itself -- this
agent reasons over prior task outputs, never reads raw evidence directly.
No Crew, Remediation Advisor, or Incident Reporter agent is defined here.
"""

from __future__ import annotations

from crewai import LLM, Agent

from app.llm_service import get_llm

ROOT_CAUSE_INVESTIGATOR_ROLE = "Root Cause Investigator"

ROOT_CAUSE_INVESTIGATOR_GOAL = (
    "Synthesize the evidence reported by the Log Analyst, Cloud Infrastructure Analyst, "
    "Kubernetes Reliability Analyst, and Knowledge/RAG Agent into the single most likely "
    "root cause of the incident, grounded strictly in what those reports actually contain."
)

ROOT_CAUSE_INVESTIGATOR_BACKSTORY = (
    "A principal engineer who leads incident postmortems and is skilled at correlating "
    "disparate signals -- logs, infrastructure metrics, Kubernetes state, and documented "
    "runbook knowledge -- into a coherent causal narrative. You reason only over the four "
    "analyst reports you are given; you never invent a metric, log line, event, or fact "
    "that is not explicitly present in them. You are careful never to confuse a symptom "
    "(elevated latency, error rates, pod restarts -- the effects everyone can see) with "
    "the root cause (the underlying condition that produced those effects). You always "
    "consider more than one explanation: for every investigation you identify credible "
    "alternative hypotheses and explain concretely, evidence by evidence, why your "
    "leading hypothesis is stronger than each of them -- never dismissing an alternative "
    "without a reason grounded in the reports. You are honest about what you don't know: "
    "you explicitly name the evidence that is missing and would make your conclusion more "
    "or less certain, rather than glossing over gaps. Your confidence score is calibrated "
    "to the actual strength and consistency of the evidence -- high only when multiple "
    "independent sources corroborate the same explanation, lower when evidence is "
    "suggestive but incomplete or contested, and never a flat 0.0 or 1.0."
)


def build_root_cause_investigator_agent(llm: LLM | None = None) -> Agent:
    """Construct the Root Cause Investigator Agent.

    Args:
        llm: LLM client to use. Defaults to the project's configured Gemini
            client (requires GOOGLE_API_KEY) if not provided -- pass an
            explicit llm (e.g. a fake, in tests) to avoid that requirement.
    """
    return Agent(
        role=ROOT_CAUSE_INVESTIGATOR_ROLE,
        goal=ROOT_CAUSE_INVESTIGATOR_GOAL,
        backstory=ROOT_CAUSE_INVESTIGATOR_BACKSTORY,
        tools=[],
        llm=llm if llm is not None else get_llm(),
        allow_delegation=False,
        verbose=False,
    )
