import pytest
from crewai import LLM

from app.agents.knowledge_rag import (
    KNOWLEDGE_RAG_BACKSTORY,
    KNOWLEDGE_RAG_GOAL,
    KNOWLEDGE_RAG_ROLE,
    build_knowledge_rag_agent,
)
from app.llm_config import MissingAPIKeyError
from app.tasks.knowledge_retrieval_task import (
    KnowledgeRetrievalReport,
    build_knowledge_retrieval_task,
)
from app.tools.knowledge_retrieval_tool import KnowledgeRetrievalTool

REQUIRED_REPORT_FIELDS = {
    "query",
    "retrieved_knowledge",
    "troubleshooting_procedures",
    "knowledge_vs_evidence_note",
    "production_safety_note",
    "summary",
    "confidence",
}


@pytest.fixture()
def fake_llm() -> LLM:
    # Construction never makes a network call, so this is safe without a real key.
    return LLM(model="gemini/gemini-2.0-flash-001", api_key="fake-test-key")


# --- Agent -----------------------------------------------------------------


def test_agent_role_goal_backstory_match_spec(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)

    assert agent.role == KNOWLEDGE_RAG_ROLE
    assert agent.goal == KNOWLEDGE_RAG_GOAL
    assert agent.backstory == KNOWLEDGE_RAG_BACKSTORY


def test_agent_goal_distinguishes_knowledge_from_evidence() -> None:
    text = KNOWLEDGE_RAG_GOAL.lower()

    assert "runbook knowledge" in text
    assert "incident-specific evidence" in text or "evidence" in text


def test_agent_backstory_covers_all_five_required_behaviors() -> None:
    text = KNOWLEDGE_RAG_BACKSTORY.lower()

    assert "cite" in text  # cite retrieved sources internally
    assert "clearly separate" in text  # distinguish knowledge from evidence
    assert "never fabricate" in text  # never fabricate runbook content
    assert "troubleshooting procedures" in text  # identify relevant procedures
    assert "production safety" in text or "read-only" in text  # respect production safety


def test_agent_uses_knowledge_retrieval_tool(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)

    assert len(agent.tools) == 1
    assert isinstance(agent.tools[0], KnowledgeRetrievalTool)


def test_agent_does_not_delegate(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)

    assert agent.allow_delegation is False


def test_build_agent_without_llm_requires_google_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError):
        build_knowledge_rag_agent()


# --- Task --------------------------------------------------------------


def test_task_is_assigned_to_the_given_agent(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)

    task = build_knowledge_retrieval_task(agent)

    assert task.agent is agent


def test_task_uses_knowledge_retrieval_tool(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)

    task = build_knowledge_retrieval_task(agent)

    assert len(task.tools) == 1
    assert isinstance(task.tools[0], KnowledgeRetrievalTool)


def test_task_expected_output_names_every_required_field(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)
    task = build_knowledge_retrieval_task(agent)

    for field_name in REQUIRED_REPORT_FIELDS:
        assert field_name in task.expected_output


def test_task_output_pydantic_schema_has_exactly_required_fields() -> None:
    assert set(KnowledgeRetrievalReport.model_fields.keys()) == REQUIRED_REPORT_FIELDS


def test_cited_knowledge_chunk_schema_supports_source_citation_and_distinction() -> None:
    from app.tasks.knowledge_retrieval_task import CitedKnowledgeChunk

    fields = set(CitedKnowledgeChunk.model_fields.keys())
    assert {
        "text",
        "source_path",
        "source_file",
        "title",
        "heading",
        "relevance_to_incident",
    }.issubset(fields)


def test_troubleshooting_procedure_schema_requires_safety_note() -> None:
    from app.tasks.knowledge_retrieval_task import TroubleshootingProcedure

    fields = set(TroubleshootingProcedure.model_fields.keys())
    assert {"description", "source_heading", "safety_note"}.issubset(fields)


def test_task_output_pydantic_is_set(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)
    task = build_knowledge_retrieval_task(agent)

    assert task.output_pydantic is KnowledgeRetrievalReport


def test_task_description_references_tool_and_forbids_invention(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)
    task = build_knowledge_retrieval_task(agent)

    assert "knowledge_retrieval_tool" in task.description
    assert "never fabricate" in task.description.lower()


def test_task_description_requires_source_citation_and_separation(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)
    task = build_knowledge_retrieval_task(agent)

    text = task.description.lower()
    assert "cite every retrieved source" in text
    assert "clearly separate from incident evidence" in text


def test_task_description_requires_respecting_production_safety(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)
    task = build_knowledge_retrieval_task(agent)

    text = task.description.lower()
    assert "production safety" in text
    assert "read-only" in text
    assert "never executes remediation" in text


def test_task_description_includes_incident_id_and_query(fake_llm: LLM) -> None:
    agent = build_knowledge_rag_agent(llm=fake_llm)

    task = build_knowledge_retrieval_task(
        agent, query="custom test query", incident_id="INC-TEST-0004"
    )

    assert "INC-TEST-0004" in task.description
    assert "custom test query" in task.description
