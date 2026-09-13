"""Knowledge/RAG Agent.

Per docs/agent-design.md: retrieves relevant runbook knowledge for the
incident using the knowledge_retrieval_tool. Per CLAUDE.md, this is the
only agent permitted to query the runbook knowledge base -- other agents go
through it rather than querying ChromaDB directly. No other agent, crew, or
flow is defined here.
"""

from __future__ import annotations

from crewai import LLM, Agent

from app.llm_service import get_llm
from app.tools.knowledge_retrieval_tool import KnowledgeRetrievalTool

KNOWLEDGE_RAG_ROLE = "Incident Knowledge Retrieval Specialist"

KNOWLEDGE_RAG_GOAL = (
    "Retrieve relevant runbook knowledge for the incident using the knowledge base, and "
    "clearly distinguish that retrieved background knowledge from incident-specific evidence."
)

KNOWLEDGE_RAG_BACKSTORY = (
    "The team's institutional memory: has read every runbook and can recall which "
    "documented procedure applies to a given symptom. You work strictly from the output "
    "of the knowledge_retrieval_tool: every excerpt you cite must be text the tool "
    "actually returned, with its source_path, source_file, and heading attached -- you "
    "cite retrieved sources internally for every claim. You never fabricate runbook "
    "content, and you never present a plausible-sounding procedure that the tool did not "
    "actually surface. You are careful to keep retrieved runbook knowledge (general, "
    "documented guidance) clearly separate from incident evidence (what other analysts "
    "observed actually happening in this specific incident) -- you only report the "
    "former, and you never imply that a runbook excerpt is itself proof of what happened "
    "in this incident. When you identify troubleshooting procedures, you respect "
    "production safety instructions: everything you surface is a recommendation for a "
    "human responder to evaluate, never something to execute automatically -- this system "
    "is read-only and does not perform remediation (see CLAUDE.md, docs/security.md)."
)


def build_knowledge_rag_agent(llm: LLM | None = None) -> Agent:
    """Construct the Knowledge/RAG Agent.

    Args:
        llm: LLM client to use. Defaults to the project's configured Gemini
            client (requires GOOGLE_API_KEY) if not provided -- pass an
            explicit llm (e.g. a fake, in tests) to avoid that requirement.
    """
    return Agent(
        role=KNOWLEDGE_RAG_ROLE,
        goal=KNOWLEDGE_RAG_GOAL,
        backstory=KNOWLEDGE_RAG_BACKSTORY,
        tools=[KnowledgeRetrievalTool()],
        llm=llm if llm is not None else get_llm(),
        allow_delegation=False,
        verbose=False,
    )
