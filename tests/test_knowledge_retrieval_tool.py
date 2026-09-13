from pathlib import Path

import pytest
from crewai.tools import BaseTool

from app.rag.ingestion import DEFAULT_RUNBOOKS_DIR
from app.tools.knowledge_retrieval_tool import KnowledgeRetrievalTool

FIXTURE_DOC = """\
# Fixture Runbook

## Zebra Migration

Zebras migrate across the savanna searching for fresh grazing land every year.

## Quantum Computing

Quantum computers use qubits and superposition to perform certain calculations.
"""


@pytest.fixture()
def fixture_runbooks_dir(tmp_path: Path) -> Path:
    runbooks_dir = tmp_path / "runbooks"
    runbooks_dir.mkdir()
    (runbooks_dir / "fixture.md").write_text(FIXTURE_DOC)
    return runbooks_dir


def test_tool_is_a_crewai_basetool() -> None:
    tool = KnowledgeRetrievalTool()

    assert isinstance(tool, BaseTool)
    assert tool.name == "knowledge_retrieval_tool"
    assert "runbook" in tool.description.lower()


def test_tool_never_claims_llm_use_for_results() -> None:
    tool = KnowledgeRetrievalTool()

    assert "no llm is used" in tool.description.lower()


def test_tool_run_returns_query_and_results(fixture_runbooks_dir: Path) -> None:
    tool = KnowledgeRetrievalTool()

    output = tool.run(
        query="qubits and superposition", n_results=1, runbooks_dir=str(fixture_runbooks_dir)
    )

    assert output["query"] == "qubits and superposition"
    assert len(output["results"]) == 1
    assert output["results"][0]["heading"] == "Quantum Computing"


def test_tool_run_results_include_source_references(fixture_runbooks_dir: Path) -> None:
    tool = KnowledgeRetrievalTool()

    output = tool.run(query="zebra migration", n_results=1, runbooks_dir=str(fixture_runbooks_dir))

    result = output["results"][0]
    assert result["source_file"] == "fixture.md"
    assert result["title"] == "Fixture Runbook"
    assert "distance" in result


def test_tool_run_never_invents_content(fixture_runbooks_dir: Path) -> None:
    raw_text = (fixture_runbooks_dir / "fixture.md").read_text()
    tool = KnowledgeRetrievalTool()

    output = tool.run(query="animals", n_results=2, runbooks_dir=str(fixture_runbooks_dir))

    for result in output["results"]:
        assert result["text"] in raw_text


def test_tool_run_works_without_any_extra_llm_configured(
    fixture_runbooks_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    tool = KnowledgeRetrievalTool()

    output = tool.run(query="zebra", n_results=1, runbooks_dir=str(fixture_runbooks_dir))

    assert len(output["results"]) == 1


def test_tool_default_runbooks_dir_reads_the_real_runbook() -> None:
    tool = KnowledgeRetrievalTool()

    output = tool.run(query="database connection pool exhaustion", n_results=3)

    assert len(output["results"]) == 3
    assert all(r["source_file"] == "database-connection-pool.md" for r in output["results"])
    raw_text = DEFAULT_RUNBOOKS_DIR.joinpath("database-connection-pool.md").read_text()
    for result in output["results"]:
        assert result["text"] in raw_text
