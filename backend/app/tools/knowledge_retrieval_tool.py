"""CrewAI-compatible wrapper around the app.rag retrieval layer.

This module only adapts app.rag.vector_store's build_runbook_collection /
retrieve to CrewAI's BaseTool contract (name, description, args_schema,
_run). All ingestion/embedding/retrieval logic lives in app/rag/ and has no
CrewAI or LLM dependency (embeddings are computed locally). Per
CLAUDE.md, this tool is the only sanctioned way to query the runbook
knowledge base -- other agents go through the Knowledge/RAG Agent rather
than querying ChromaDB directly. Not wired to any Agent, Crew, or Flow yet.
"""

from __future__ import annotations

from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.rag.ingestion import DEFAULT_RUNBOOKS_DIR
from app.rag.vector_store import build_runbook_collection, retrieve

# Empirically calibrated against this project's runbook corpus and
# embedding model (all-MiniLM-L6-v2): genuinely relevant queries score
# ~0.7-0.8; a wholly unrelated query still scores ~2.0+ against the
# closest chunk, since Chroma always returns *a* closest match regardless
# of how weak it is. 1.5 sits well clear of both, rejecting no-good-match
# queries instead of returning a poor match as if it were relevant --
# see docs/evaluation.md's "hallucination resistance" evaluation.
DEFAULT_MAX_DISTANCE = 1.5


class KnowledgeRetrievalToolInput(BaseModel):
    query: str = Field(
        description="The topic, symptom, or question to retrieve relevant runbook knowledge for."
    )
    n_results: int = Field(
        default=3, description="Maximum number of runbook chunks to retrieve."
    )
    runbooks_dir: str | None = Field(
        default=None,
        description="Override the runbooks directory to ingest from. Defaults to data/runbooks/.",
    )
    max_distance: float | None = Field(
        default=DEFAULT_MAX_DISTANCE,
        description="Reject matches weaker than this distance instead of returning a poor "
        "match as if it were relevant. Pass null to disable filtering.",
    )


class KnowledgeRetrievalTool(BaseTool):
    """Retrieves the most relevant runbook knowledge chunks for a query via
    local similarity search over data/runbooks/ (ChromaDB). Uses no LLM.
    Every result includes its exact source document, section heading, and
    verbatim text -- this tool never invents runbook content.
    """

    name: str = "knowledge_retrieval_tool"
    description: str = (
        "Retrieves the most relevant runbook knowledge chunks for a query from the "
        "ChromaDB-backed runbook knowledge base (data/runbooks/), using local similarity "
        "search -- no LLM is used to produce results. Every result includes its exact "
        "source_path, source_file, title, heading, and verbatim text, so findings are "
        "always traceable back to the source runbook. This tool never invents runbook "
        "content: it only returns text that is actually present in the source files. "
        "Weak/unrelated matches are filtered out by default (see max_distance) rather "
        "than returned as if they were relevant -- an empty results list means no "
        "runbook in the knowledge base actually covers the query."
    )
    args_schema: type[BaseModel] = KnowledgeRetrievalToolInput

    def _run(
        self,
        query: str,
        n_results: int = 3,
        runbooks_dir: str | None = None,
        max_distance: float | None = DEFAULT_MAX_DISTANCE,
    ) -> dict:
        collection = build_runbook_collection(
            persist_directory=None,
            runbooks_dir=Path(runbooks_dir) if runbooks_dir else DEFAULT_RUNBOOKS_DIR,
        )
        results = retrieve(collection, query, n_results=n_results, max_distance=max_distance)
        return {"query": query, "results": [r.to_dict() for r in results]}
