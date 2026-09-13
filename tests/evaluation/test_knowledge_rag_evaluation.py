"""Golden-scenario evaluation for the Knowledge/RAG Agent against the real
runbook knowledge base (see docs/evaluation.md).

This exercises a real LLM call via the Knowledge/RAG Agent + Knowledge
Retrieval Task (no Crew involved -- Task.execute_sync runs a single task
against a single agent). It requires a real GOOGLE_API_KEY and is skipped
gracefully without one, per the project's "handle missing API keys
gracefully" rule.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.agents.knowledge_rag import build_knowledge_rag_agent
from app.llm_config import is_configured
from app.rag.ingestion import DEFAULT_RUNBOOKS_DIR
from app.tasks.knowledge_retrieval_task import (
    DEFAULT_QUERY,
    KnowledgeRetrievalReport,
    build_knowledge_retrieval_task,
)
from app.tools.knowledge_retrieval_tool import KnowledgeRetrievalTool

RUNBOOK_TEXT = DEFAULT_RUNBOOKS_DIR.joinpath("database-connection-pool.md").read_text()

pytestmark = [
    pytest.mark.live_llm,
    pytest.mark.skipif(
        not is_configured(),
        reason=(
            "GOOGLE_API_KEY is not set -- skipping live Knowledge/RAG Agent evaluation. "
            "Set it in backend/.env to run this evaluation against a real model."
        ),
    ),
]


@pytest.fixture(scope="module")
def evaluation_result() -> KnowledgeRetrievalReport:
    agent = build_knowledge_rag_agent()
    task = build_knowledge_retrieval_task(agent)
    output = task.execute_sync(agent=agent)

    assert output.pydantic is not None, "Task did not produce structured output"
    return output.pydantic


@pytest.fixture(scope="module")
def ground_truth() -> dict:
    # The tool's own direct output is the ground truth the agent must not deviate from.
    tool = KnowledgeRetrievalTool()
    return tool.run(query=DEFAULT_QUERY, n_results=3)


def test_agent_retrieves_at_least_one_knowledge_chunk(
    evaluation_result: KnowledgeRetrievalReport,
) -> None:
    assert len(evaluation_result.retrieved_knowledge) > 0


def test_agent_cites_source_for_every_retrieved_chunk(
    evaluation_result: KnowledgeRetrievalReport,
) -> None:
    for chunk in evaluation_result.retrieved_knowledge:
        assert chunk.source_path.strip() != ""
        assert chunk.source_file.strip() != ""
        assert chunk.heading.strip() != ""


def test_agent_identifies_troubleshooting_procedures(
    evaluation_result: KnowledgeRetrievalReport,
) -> None:
    assert len(evaluation_result.troubleshooting_procedures) > 0


def test_agent_every_procedure_has_a_safety_note(
    evaluation_result: KnowledgeRetrievalReport,
) -> None:
    for procedure in evaluation_result.troubleshooting_procedures:
        assert procedure.safety_note.strip() != ""


def test_agent_production_safety_note_reflects_read_only_system(
    evaluation_result: KnowledgeRetrievalReport,
) -> None:
    text = evaluation_result.production_safety_note.lower()
    assert any(
        phrase in text
        for phrase in ("read-only", "read only", "advisory", "human", "does not execute", "not execute")
    )


def test_agent_distinguishes_knowledge_from_incident_evidence(
    evaluation_result: KnowledgeRetrievalReport,
) -> None:
    assert evaluation_result.knowledge_vs_evidence_note.strip() != ""


def test_agent_reports_confidence_in_valid_range(
    evaluation_result: KnowledgeRetrievalReport,
) -> None:
    assert 0.0 <= evaluation_result.confidence <= 1.0


def test_agent_summary_is_non_empty(evaluation_result: KnowledgeRetrievalReport) -> None:
    assert evaluation_result.summary.strip() != ""


def test_agent_never_fabricates_retrieved_text(
    evaluation_result: KnowledgeRetrievalReport,
) -> None:
    for chunk in evaluation_result.retrieved_knowledge:
        assert chunk.text in RUNBOOK_TEXT, (
            f"Retrieved chunk text not found verbatim in the source runbook: {chunk.text!r}"
        )


def test_agent_retrieved_sources_match_tool_ground_truth(
    evaluation_result: KnowledgeRetrievalReport, ground_truth: dict
) -> None:
    known_texts = {r["text"] for r in ground_truth["results"]}

    for chunk in evaluation_result.retrieved_knowledge:
        assert chunk.text in known_texts, (
            f"Agent cited a chunk the tool did not actually return: {chunk.text!r}"
        )
