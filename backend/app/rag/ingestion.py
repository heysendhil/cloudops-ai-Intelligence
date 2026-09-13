"""Document ingestion and chunking for the RAG layer.

No ChromaDB, no LLM: this module only reads Markdown files from disk and
splits them into chunks. Every chunk's text is an exact substring of the
source file it came from -- nothing is rewritten, summarized, or invented.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUNBOOKS_DIR = REPO_ROOT / "data" / "runbooks"

_H1_PATTERN = re.compile(r"(?m)^# (.+)$")
_H2_PATTERN = re.compile(r"(?m)^## (.+)$")


@dataclass(frozen=True)
class DocumentChunk:
    """One chunk of a source document. `text` is always an exact substring
    of the original file at `source_path` -- the evidence reference for
    "never invent document content"."""

    chunk_id: str
    text: str
    source_path: str
    source_file: str
    title: str | None
    heading: str
    chunk_index: int

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source_path": self.source_path,
            "source_file": self.source_file,
            "title": self.title,
            "heading": self.heading,
            "chunk_index": self.chunk_index,
        }


def load_markdown_documents(directory: Path | str = DEFAULT_RUNBOOKS_DIR) -> list[tuple[Path, str]]:
    """Read every *.md file in `directory`, sorted by filename for
    determinism. Returns (path, raw_text) pairs -- raw_text is the file's
    exact content, unmodified.
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise FileNotFoundError(f"Runbooks directory not found: {dir_path}")

    return [(path, path.read_text(encoding="utf-8")) for path in sorted(dir_path.glob("*.md"))]


def _extract_title(text: str) -> str | None:
    match = _H1_PATTERN.search(text)
    return match.group(1).strip() if match else None


def chunk_markdown(
    path: Path, text: str, repo_root: Path = REPO_ROOT
) -> list[DocumentChunk]:
    """Split a Markdown document's text into chunks along its level-2 ("## ")
    section headings. Each chunk's `text` is an exact slice of `text` -- no
    content is rewritten or summarized. Falls back to a single whole-document
    chunk if there are no level-2 headings.
    """
    try:
        source_path = str(path.relative_to(repo_root))
    except ValueError:
        source_path = str(path)
    source_file = path.name
    title = _extract_title(text)

    section_matches = list(_H2_PATTERN.finditer(text))
    chunks: list[DocumentChunk] = []
    chunk_index = 0

    if not section_matches:
        stripped = text.strip()
        if stripped:
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{source_file}::chunk-0",
                    text=text,
                    source_path=source_path,
                    source_file=source_file,
                    title=title,
                    heading=title or source_file,
                    chunk_index=0,
                )
            )
        return chunks

    # Content before the first "## " heading (e.g. the "# Title" line) is
    # only kept as its own chunk if it has real content beyond the title.
    preamble = text[: section_matches[0].start()]
    preamble_without_title = _H1_PATTERN.sub("", preamble).strip()
    if preamble_without_title:
        chunks.append(
            DocumentChunk(
                chunk_id=f"{source_file}::chunk-{chunk_index}",
                text=preamble,
                source_path=source_path,
                source_file=source_file,
                title=title,
                heading=title or "Preamble",
                chunk_index=chunk_index,
            )
        )
        chunk_index += 1

    for i, match in enumerate(section_matches):
        start = match.start()
        end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(text)
        section_text = text[start:end]
        chunks.append(
            DocumentChunk(
                chunk_id=f"{source_file}::chunk-{chunk_index}",
                text=section_text,
                source_path=source_path,
                source_file=source_file,
                title=title,
                heading=match.group(1).strip(),
                chunk_index=chunk_index,
            )
        )
        chunk_index += 1

    return chunks


def load_and_chunk_documents(
    directory: Path | str = DEFAULT_RUNBOOKS_DIR,
) -> list[DocumentChunk]:
    """Convenience: load every Markdown file in `directory` and chunk each one."""
    chunks: list[DocumentChunk] = []
    for path, text in load_markdown_documents(directory):
        chunks.extend(chunk_markdown(path, text))
    return chunks
