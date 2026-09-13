from pathlib import Path

import pytest

from app.rag.ingestion import DEFAULT_RUNBOOKS_DIR, load_and_chunk_documents
from app.rag.vector_store import (
    build_runbook_collection,
    get_chroma_client,
    get_or_create_collection,
    ingest_runbooks,
    retrieve,
)

# Deliberately unrelated topics per section, so similarity search has an
# unambiguous, deterministic "correct" answer for a topic-specific query.
FIXTURE_DOC = """\
# Fixture Runbook

## Zebra Migration

Zebras migrate across the savanna searching for fresh grazing land every year, \
often traveling hundreds of kilometers alongside wildebeest herds.

## Quantum Computing

Quantum computers use qubits and superposition to perform certain calculations \
far faster than classical bits ever could for specific problem classes.

## Castle Architecture

Medieval castles used thick stone walls, moats, and battlements for defense \
against siege engines and prolonged attacks.
"""


@pytest.fixture()
def fixture_runbooks_dir(tmp_path: Path) -> Path:
    runbooks_dir = tmp_path / "runbooks"
    runbooks_dir.mkdir()
    (runbooks_dir / "fixture.md").write_text(FIXTURE_DOC)
    return runbooks_dir


@pytest.fixture()
def fixture_collection(fixture_runbooks_dir: Path):
    client = get_chroma_client(persist_directory=None)  # ephemeral, isolated per test
    collection = get_or_create_collection(client, name="fixture-runbooks")
    ingest_runbooks(collection, fixture_runbooks_dir)
    return collection


# --- ingestion into the vector store -------------------------------------


def test_ingest_runbooks_adds_one_entry_per_chunk(
    fixture_collection, fixture_runbooks_dir: Path
) -> None:
    expected_chunks = load_and_chunk_documents(fixture_runbooks_dir)

    assert fixture_collection.count() == len(expected_chunks) == 3


def test_ingest_runbooks_empty_directory_adds_nothing(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty-runbooks"
    empty_dir.mkdir()
    client = get_chroma_client(persist_directory=None)
    collection = get_or_create_collection(client, name="empty-runbooks")

    chunks = ingest_runbooks(collection, empty_dir)

    assert chunks == []
    assert collection.count() == 0


def test_ingest_runbooks_returns_the_chunks_it_added(
    fixture_runbooks_dir: Path,
) -> None:
    client = get_chroma_client(persist_directory=None)
    collection = get_or_create_collection(client, name="fixture-runbooks-2")

    chunks = ingest_runbooks(collection, fixture_runbooks_dir)

    assert {c.heading for c in chunks} == {"Zebra Migration", "Quantum Computing", "Castle Architecture"}


def test_build_runbook_collection_is_idempotent_on_a_persistent_client(
    fixture_runbooks_dir: Path, tmp_path: Path
) -> None:
    persist_dir = tmp_path / "chroma-persist"

    first = build_runbook_collection(persist_directory=persist_dir, runbooks_dir=fixture_runbooks_dir)
    assert first.count() == 3

    second = build_runbook_collection(persist_directory=persist_dir, runbooks_dir=fixture_runbooks_dir)
    assert second.count() == 3  # not duplicated by re-running


# --- similarity retrieval -------------------------------------------------


def test_retrieve_finds_the_semantically_relevant_chunk(fixture_collection) -> None:
    results = retrieve(fixture_collection, "qubits and superposition in quantum computers", n_results=1)

    assert len(results) == 1
    assert results[0].heading == "Quantum Computing"


def test_retrieve_orders_results_by_relevance(fixture_collection) -> None:
    results = retrieve(fixture_collection, "medieval siege defenses and castle walls", n_results=3)

    assert results[0].heading == "Castle Architecture"
    # distances should be non-decreasing (most similar first)
    distances = [r.distance for r in results]
    assert distances == sorted(distances)


def test_retrieve_respects_n_results(fixture_collection) -> None:
    results = retrieve(fixture_collection, "animals migrating", n_results=2)

    assert len(results) == 2


def test_retrieve_on_empty_collection_returns_empty_list_not_error() -> None:
    client = get_chroma_client(persist_directory=None)
    collection = get_or_create_collection(client, name="truly-empty")

    results = retrieve(collection, "anything at all")

    assert results == []


# --- source attribution -------------------------------------------------


def test_retrieve_returns_source_document_references(fixture_collection) -> None:
    results = retrieve(fixture_collection, "quantum qubits", n_results=1)

    result = results[0]
    assert result.source_file == "fixture.md"
    # fixture dir lives under tmp_path, outside REPO_ROOT, so chunk_markdown's
    # relative-path fallback correctly reports the absolute path here.
    assert result.source_path.endswith("fixture.md")
    assert result.title == "Fixture Runbook"
    assert result.heading == "Quantum Computing"


def test_retrieve_text_is_verbatim_from_the_source_file_never_invented(
    fixture_collection, fixture_runbooks_dir: Path
) -> None:
    raw_text = (fixture_runbooks_dir / "fixture.md").read_text()

    results = retrieve(fixture_collection, "castle walls and moats", n_results=3)

    for result in results:
        assert result.text in raw_text


# --- real Phase 3 runbook data --------------------------------------------


def test_real_runbook_ingestion_and_retrieval_end_to_end() -> None:
    client = get_chroma_client(persist_directory=None)
    collection = get_or_create_collection(client, name="real-runbooks")

    chunks = ingest_runbooks(collection, DEFAULT_RUNBOOKS_DIR)
    assert len(chunks) == 7
    assert collection.count() == 7

    results = retrieve(
        collection, "why does a database connection pool become exhausted", n_results=3
    )
    assert len(results) == 3
    assert all(r.source_file == "database-connection-pool.md" for r in results)
    # the Likely Causes / Symptoms sections should rank ahead of References
    assert "References" not in {r.heading for r in results}


def test_real_runbook_retrieval_returns_source_references() -> None:
    client = get_chroma_client(persist_directory=None)
    collection = get_or_create_collection(client, name="real-runbooks-2")
    ingest_runbooks(collection, DEFAULT_RUNBOOKS_DIR)

    results = retrieve(collection, "liveness probe failures causing pod restarts", n_results=1)

    assert results[0].source_path == "data/runbooks/database-connection-pool.md"
    assert results[0].title == "Runbook: Database Connection Pool Exhaustion"


def test_real_runbook_retrieval_never_invents_content() -> None:
    raw_text = DEFAULT_RUNBOOKS_DIR.joinpath("database-connection-pool.md").read_text()
    client = get_chroma_client(persist_directory=None)
    collection = get_or_create_collection(client, name="real-runbooks-3")
    ingest_runbooks(collection, DEFAULT_RUNBOOKS_DIR)

    results = retrieve(collection, "mitigation steps for connection pool exhaustion", n_results=7)

    assert len(results) == 7
    for result in results:
        assert result.text in raw_text
