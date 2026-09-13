"""ChromaDB-backed vector store for the RAG layer: embeddings, ingestion into
a collection, and similarity retrieval with source references.

No LLM call is involved -- embeddings are produced locally by ChromaDB's
default sentence-transformer (ONNX) embedding function. This module does not
define a CrewAI tool or agent; it is the underlying retrieval capability
only (see docs/agent-design.md: the Knowledge/RAG Agent, not built yet,
will be the only agent permitted to query this).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from app.rag.ingestion import (
    DEFAULT_RUNBOOKS_DIR,
    DocumentChunk,
    load_and_chunk_documents,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PERSIST_DIR = REPO_ROOT / "rag" / "chroma_db"
COLLECTION_NAME = "runbooks"


def get_chroma_client(persist_directory: Path | str | None = None) -> Any:
    """Return a Chroma client. Pass `persist_directory` for durable, on-disk
    storage (e.g. DEFAULT_PERSIST_DIR); omit it for an in-memory client.

    Note: separate EphemeralClient() instances in this Chroma version share
    the same default tenant/database, so callers that need true isolation
    between calls (e.g. tests) must also use distinct collection names --
    see build_runbook_collection(), which does this automatically.
    """
    if persist_directory is None:
        return chromadb.EphemeralClient()
    return chromadb.PersistentClient(path=str(persist_directory))


def get_or_create_collection(
    client: Any, name: str = COLLECTION_NAME, embedding_function: Any | None = None
) -> Collection:
    return client.get_or_create_collection(
        name=name, embedding_function=embedding_function or DefaultEmbeddingFunction()
    )


def ingest_runbooks(
    collection: Collection, runbooks_dir: Path | str = DEFAULT_RUNBOOKS_DIR
) -> list[DocumentChunk]:
    """Load, chunk, and add every runbook in `runbooks_dir` to `collection`.
    Returns the chunks that were ingested. Adds nothing (and makes no
    embedding calls) if the directory has no documents.
    """
    chunks = load_and_chunk_documents(runbooks_dir)
    if not chunks:
        return []

    collection.add(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        metadatas=[
            {
                "source_path": chunk.source_path,
                "source_file": chunk.source_file,
                "title": chunk.title or "",
                "heading": chunk.heading,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ],
    )
    return chunks


def build_runbook_collection(
    persist_directory: Path | str | None = None,
    runbooks_dir: Path | str = DEFAULT_RUNBOOKS_DIR,
) -> Collection:
    """Get (or create + ingest) the runbook collection. With a persistent
    client this is idempotent -- ingestion only runs if the collection is
    currently empty, so re-running does not duplicate chunks. With no
    persist_directory (ephemeral), each call gets its own uniquely-named
    collection so separate calls never see each other's data.
    """
    client = get_chroma_client(persist_directory)
    name = COLLECTION_NAME if persist_directory is not None else f"{COLLECTION_NAME}-{uuid4().hex}"
    collection = get_or_create_collection(client, name=name)
    if collection.count() == 0:
        ingest_runbooks(collection, runbooks_dir)
    return collection


@dataclass(frozen=True)
class RetrievalResult:
    """One retrieved chunk, with its source document reference and
    similarity distance (lower = more similar)."""

    text: str
    source_path: str
    source_file: str
    title: str
    heading: str
    chunk_index: int
    distance: float | None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "source_path": self.source_path,
            "source_file": self.source_file,
            "title": self.title,
            "heading": self.heading,
            "chunk_index": self.chunk_index,
            "distance": self.distance,
        }


def retrieve(
    collection: Collection,
    query: str,
    n_results: int = 3,
    max_distance: float | None = None,
) -> list[RetrievalResult]:
    """Similarity-search `collection` for `query`. Returns [] if the
    collection is empty rather than raising or fabricating a result.

    `max_distance`, if given, drops results whose distance exceeds it --
    Chroma's default behavior is to always return the closest `n_results`
    regardless of how weak the match actually is, which is a real
    hallucination risk for a query that has no good match in the corpus at
    all (e.g. a totally unrelated topic still "matches" the closest
    runbook chunk, just at a much higher distance -- observed empirically
    around 2.0+ for an unrelated query against this project's runbook
    corpus, versus ~0.7-0.8 for a genuinely relevant one). None (the
    default) preserves the original always-return-top-N behavior, for
    callers that want it.
    """
    count = collection.count()
    if count == 0:
        return []

    raw = collection.query(query_texts=[query], n_results=min(n_results, count))

    documents = raw.get("documents") or [[]]
    metadatas = raw.get("metadatas") or [[]]
    distances = raw.get("distances") or [[]]

    results = []
    for text, metadata, distance in zip(
        documents[0], metadatas[0], distances[0] or [None] * len(documents[0])
    ):
        if max_distance is not None and distance is not None and distance > max_distance:
            continue
        results.append(
            RetrievalResult(
                text=text,
                source_path=metadata.get("source_path", ""),
                source_file=metadata.get("source_file", ""),
                title=metadata.get("title", ""),
                heading=metadata.get("heading", ""),
                chunk_index=metadata.get("chunk_index", 0),
                distance=distance,
            )
        )
    return results
