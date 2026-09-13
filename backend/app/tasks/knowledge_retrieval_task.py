"""Knowledge Retrieval Task, executed by the Knowledge/RAG Agent.

Per docs/agent-design.md task #4 (Knowledge Retrieval Task). Defines a
strict, structured expected output that keeps retrieved runbook knowledge
clearly separate from incident-specific evidence, cites every source, and
frames any troubleshooting procedure as advisory-only (V1 is read-only --
see CLAUDE.md, docs/security.md). No crew or flow is defined here.
"""

from __future__ import annotations

from crewai import Agent, Task
from pydantic import BaseModel, Field

from app.tools.knowledge_retrieval_tool import KnowledgeRetrievalTool

DEFAULT_INCIDENT_ID = "INC-2026-0912"
DEFAULT_QUERY = (
    "database connection pool exhaustion causing elevated latency, HTTP 500 errors, "
    "and pod restarts"
)


class CitedKnowledgeChunk(BaseModel):
    text: str = Field(description="Verbatim runbook excerpt, exactly as returned by the tool.")
    source_path: str = Field(description="Source file path, verbatim from the tool.")
    source_file: str = Field(description="Source file name, verbatim from the tool.")
    title: str = Field(description="Runbook title, verbatim from the tool.")
    heading: str = Field(description="Section heading this excerpt came from, verbatim from the tool.")
    relevance_to_incident: str = Field(
        description="The agent's own brief note on why this excerpt is relevant to the "
        "incident query -- explicitly the agent's interpretation, not part of the "
        "verbatim excerpt."
    )


class TroubleshootingProcedure(BaseModel):
    description: str = Field(
        description="The troubleshooting/diagnosis/mitigation step, grounded in retrieved text."
    )
    source_heading: str = Field(description="Which retrieved runbook section this came from.")
    safety_note: str = Field(
        description="Explicit statement that this is advisory only and requires human "
        "review -- this system does not execute remediation automatically."
    )


class KnowledgeRetrievalReport(BaseModel):
    query: str = Field(description="The query used to retrieve runbook knowledge.")
    retrieved_knowledge: list[CitedKnowledgeChunk] = Field(default_factory=list)
    troubleshooting_procedures: list[TroubleshootingProcedure] = Field(default_factory=list)
    knowledge_vs_evidence_note: str = Field(
        description="Explicit statement that everything in retrieved_knowledge and "
        "troubleshooting_procedures is general background knowledge from runbooks, not "
        "confirmed facts about what happened in this specific incident."
    )
    production_safety_note: str = Field(
        description="Explicit statement that any procedures surfaced are recommendations "
        "for a human to evaluate, never instructions this system will execute."
    )
    summary: str = Field(description="Short prose summary of the retrieved knowledge.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence (0.0-1.0) that the retrieved knowledge is relevant to the query.",
    )


EXPECTED_OUTPUT = (
    "A structured knowledge retrieval report with exactly these fields: "
    "'query' -- the query used with the knowledge_retrieval_tool; "
    "'retrieved_knowledge' -- every relevant excerpt the tool returned, each with its "
    "verbatim text, source_path, source_file, title, heading, and a relevance_to_incident "
    "note (clearly the agent's own interpretation, not part of the excerpt); "
    "'troubleshooting_procedures' -- relevant troubleshooting/diagnosis/mitigation "
    "procedures identified in the retrieved knowledge, each with a safety_note stating it "
    "is advisory only; "
    "'knowledge_vs_evidence_note' -- an explicit statement that everything retrieved is "
    "general runbook knowledge, not confirmed facts about this specific incident; "
    "'production_safety_note' -- an explicit statement that any procedure is a "
    "recommendation for human review, never something this system executes automatically; "
    "'summary' -- a short prose summary; and "
    "'confidence' -- a number between 0.0 and 1.0. "
    "Every cited excerpt and source reference must be exactly what the "
    "knowledge_retrieval_tool returned -- never invent runbook content, a source, or a "
    "procedure the tool did not surface."
)


def build_knowledge_retrieval_task(
    agent: Agent,
    query: str = DEFAULT_QUERY,
    n_results: int = 3,
    runbooks_dir: str | None = None,
    incident_id: str = DEFAULT_INCIDENT_ID,
) -> Task:
    """Build the Knowledge Retrieval Task for the given (already-constructed) agent."""
    tool_call_instruction = (
        f"Call the knowledge_retrieval_tool with query='{query}', n_results={n_results}"
        + (f", runbooks_dir='{runbooks_dir}'" if runbooks_dir else "")
    )

    description = (
        f"Support the investigation of incident {incident_id} by retrieving relevant "
        f"runbook knowledge. {tool_call_instruction} to search the runbook knowledge base. "
        "Cite every retrieved source internally: for each excerpt you use, record its "
        "exact source_path, source_file, title, and heading alongside the verbatim text. "
        "Identify any troubleshooting, diagnosis, or mitigation procedures the retrieved "
        "excerpts describe. You must keep retrieved runbook knowledge clearly separate "
        "from incident evidence -- this task only produces general background knowledge "
        "from the knowledge base; it does not confirm what actually happened in this "
        "incident, which is the job of the other analyst agents. Never fabricate runbook "
        "content: only report text, sources, or procedures the tool actually returned. "
        "Respect production safety instructions: this system is read-only and never "
        "executes remediation, so present every procedure as a recommendation for a "
        "human to evaluate, not as an instruction that will be carried out."
    )

    return Task(
        description=description,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        tools=[KnowledgeRetrievalTool()],
        output_pydantic=KnowledgeRetrievalReport,
    )
