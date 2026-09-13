from pathlib import Path

import pytest

from app.rag.ingestion import (
    DEFAULT_RUNBOOKS_DIR,
    chunk_markdown,
    load_and_chunk_documents,
    load_markdown_documents,
)

FIXTURE_DOC = """\
# Fixture Runbook

## First Section

First section body text.
More detail here.

## Second Section

Second section body text.

## Third Section

Third section body text.
"""

NO_HEADINGS_DOC = "Just a single block of text with no markdown headings at all.\n"


@pytest.fixture()
def fixture_runbooks_dir(tmp_path: Path) -> Path:
    runbooks_dir = tmp_path / "runbooks"
    runbooks_dir.mkdir()
    (runbooks_dir / "fixture.md").write_text(FIXTURE_DOC)
    (runbooks_dir / "no-headings.md").write_text(NO_HEADINGS_DOC)
    # non-markdown file that must be ignored
    (runbooks_dir / "notes.txt").write_text("should not be loaded")
    return runbooks_dir


# --- loading ---------------------------------------------------------------


def test_load_markdown_documents_reads_only_md_files(fixture_runbooks_dir: Path) -> None:
    documents = load_markdown_documents(fixture_runbooks_dir)

    names = {path.name for path, _ in documents}
    assert names == {"fixture.md", "no-headings.md"}


def test_load_markdown_documents_returns_exact_file_content(fixture_runbooks_dir: Path) -> None:
    documents = load_markdown_documents(fixture_runbooks_dir)

    text_by_name = {path.name: text for path, text in documents}
    assert text_by_name["fixture.md"] == FIXTURE_DOC


def test_load_markdown_documents_sorted_for_determinism(fixture_runbooks_dir: Path) -> None:
    documents = load_markdown_documents(fixture_runbooks_dir)

    names = [path.name for path, _ in documents]
    assert names == sorted(names)


def test_load_markdown_documents_missing_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_markdown_documents(tmp_path / "does-not-exist")


# --- chunking ----------------------------------------------------------


def test_chunk_markdown_splits_by_h2_headings(fixture_runbooks_dir: Path) -> None:
    path = fixture_runbooks_dir / "fixture.md"
    text = path.read_text()

    chunks = chunk_markdown(path, text, repo_root=fixture_runbooks_dir)

    assert [c.heading for c in chunks] == ["First Section", "Second Section", "Third Section"]
    assert [c.chunk_index for c in chunks] == [0, 1, 2]


def test_chunk_markdown_extracts_document_title(fixture_runbooks_dir: Path) -> None:
    path = fixture_runbooks_dir / "fixture.md"
    text = path.read_text()

    chunks = chunk_markdown(path, text, repo_root=fixture_runbooks_dir)

    assert all(c.title == "Fixture Runbook" for c in chunks)


def test_chunk_text_is_exact_substring_of_source_never_invented(fixture_runbooks_dir: Path) -> None:
    path = fixture_runbooks_dir / "fixture.md"
    text = path.read_text()

    chunks = chunk_markdown(path, text, repo_root=fixture_runbooks_dir)

    for chunk in chunks:
        assert chunk.text in text
        # each chunk must contain its own heading line verbatim
        assert f"## {chunk.heading}" in chunk.text


def test_chunk_ids_are_unique(fixture_runbooks_dir: Path) -> None:
    path = fixture_runbooks_dir / "fixture.md"
    text = path.read_text()

    chunks = chunk_markdown(path, text, repo_root=fixture_runbooks_dir)

    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_chunk_metadata_includes_source_path(fixture_runbooks_dir: Path) -> None:
    path = fixture_runbooks_dir / "fixture.md"
    text = path.read_text()

    chunks = chunk_markdown(path, text, repo_root=fixture_runbooks_dir)

    assert all(c.source_path == "fixture.md" for c in chunks)
    assert all(c.source_file == "fixture.md" for c in chunks)


def test_chunk_markdown_falls_back_to_whole_document_without_h2_headings(
    fixture_runbooks_dir: Path,
) -> None:
    path = fixture_runbooks_dir / "no-headings.md"
    text = path.read_text()

    chunks = chunk_markdown(path, text, repo_root=fixture_runbooks_dir)

    assert len(chunks) == 1
    assert chunks[0].text == text


def test_chunk_markdown_empty_document_yields_no_chunks(tmp_path: Path) -> None:
    empty_path = tmp_path / "empty.md"
    empty_path.write_text("")

    chunks = chunk_markdown(empty_path, "", repo_root=tmp_path)

    assert chunks == []


def test_load_and_chunk_documents_covers_all_files(fixture_runbooks_dir: Path) -> None:
    chunks = load_and_chunk_documents(fixture_runbooks_dir)

    source_files = {c.source_file for c in chunks}
    assert source_files == {"fixture.md", "no-headings.md"}
    assert len(chunks) == 3 + 1  # 3 sections + 1 fallback whole-document chunk


# --- real Phase 3 runbook -----------------------------------------------


def test_real_runbook_directory_is_the_default() -> None:
    assert DEFAULT_RUNBOOKS_DIR.name == "runbooks"
    assert (DEFAULT_RUNBOOKS_DIR / "database-connection-pool.md").is_file()


def test_real_runbook_chunks_exactly_by_its_seven_sections() -> None:
    chunks = load_and_chunk_documents()

    assert [c.heading for c in chunks] == [
        "Overview",
        "Symptoms",
        "Likely Causes",
        "Diagnosis Steps",
        "Mitigation",
        "Prevention",
        "References",
    ]
    assert all(c.title == "Runbook: Database Connection Pool Exhaustion" for c in chunks)
    assert all(c.source_file == "database-connection-pool.md" for c in chunks)


def test_real_runbook_chunk_text_is_verbatim_from_disk() -> None:
    raw_text = DEFAULT_RUNBOOKS_DIR.joinpath("database-connection-pool.md").read_text()

    chunks = load_and_chunk_documents()

    for chunk in chunks:
        assert chunk.text in raw_text
