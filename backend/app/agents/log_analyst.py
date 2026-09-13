"""Log Analyst Agent.

Per docs/agent-design.md: analyzes application/system log evidence for the
incident window and reports only what the Log Analysis Tool actually finds
in the log file -- no other agent, crew, or flow is defined here.
"""

from __future__ import annotations

from crewai import LLM, Agent

from app.llm_service import get_llm
from app.tools.log_analysis_tool import LogAnalysisTool

LOG_ANALYST_ROLE = "Log Analyst"

LOG_ANALYST_GOAL = "Analyze application logs and identify evidence relevant to the incident."

LOG_ANALYST_BACKSTORY = (
    "A senior SRE who has spent years reading application and system logs to find the "
    "first sign of trouble before it becomes an outage. You work strictly from the "
    "output of the log_analysis_tool: every error, warning, pattern, and timestamp you "
    "report must trace back to a specific line the tool returned. You never speculate, "
    "paraphrase away detail, or add a finding that the tool did not surface -- if the "
    "tool found nothing for a category, you report it as empty rather than inventing "
    "something plausible-sounding."
)


def build_log_analyst_agent(llm: LLM | None = None) -> Agent:
    """Construct the Log Analyst Agent.

    Args:
        llm: LLM client to use. Defaults to the project's configured Gemini
            client (requires GOOGLE_API_KEY) if not provided -- pass an
            explicit llm (e.g. a fake, in tests) to avoid that requirement.
    """
    return Agent(
        role=LOG_ANALYST_ROLE,
        goal=LOG_ANALYST_GOAL,
        backstory=LOG_ANALYST_BACKSTORY,
        tools=[LogAnalysisTool()],
        llm=llm if llm is not None else get_llm(),
        allow_delegation=False,
        verbose=False,
    )
