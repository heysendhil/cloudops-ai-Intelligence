"""CrewAI-compatible wrapper around the log_parser core.

This module only adapts LogAnalyzer to CrewAI's BaseTool contract (name,
description, args_schema, _run). All actual log reading/parsing logic lives
in log_parser.py and has no CrewAI or LLM dependency -- this tool is not
wired to any Agent, Crew, or Flow yet.
"""

from __future__ import annotations

from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.tools.log_parser import DEFAULT_LOG_PATH, LogAnalyzer


class LogAnalysisToolInput(BaseModel):
    log_path: str | None = Field(
        default=None,
        description="Path to the log file to analyze. Defaults to data/logs/payment-api.log.",
    )
    start_time: str | None = Field(
        default=None,
        description=(
            "ISO 8601 UTC start of the incident time window to filter to, "
            "e.g. 2026-09-12T13:50:00Z. Omit to include the whole file."
        ),
    )
    end_time: str | None = Field(
        default=None,
        description="ISO 8601 UTC end of the incident time window to filter to.",
    )
    min_pattern_occurrences: int = Field(
        default=2,
        description="Minimum occurrences for a normalized message to be reported as a repeated pattern.",
    )


class LogAnalysisTool(BaseTool):
    """Reads an application log file and extracts ERROR/WARN entries,
    repeated message patterns, and timestamps, filtered to an incident time
    window. Every finding includes a line number and the exact raw log line
    it came from -- this tool never invents or paraphrases log content, and
    runs entirely without an LLM.
    """

    name: str = "log_analysis_tool"
    description: str = (
        "Reads a CloudOps application log file, filters entries to an incident time "
        "window, and extracts ERROR entries, WARN entries, repeated message patterns, "
        "and timestamps. Every result item includes a line number and the exact raw "
        "log line it came from -- it never invents or paraphrases log content."
    )
    args_schema: type[BaseModel] = LogAnalysisToolInput

    def _run(
        self,
        log_path: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        min_pattern_occurrences: int = 2,
    ) -> dict:
        analyzer = LogAnalyzer(Path(log_path) if log_path else DEFAULT_LOG_PATH)
        result = analyzer.analyze(
            start_time=start_time,
            end_time=end_time,
            min_pattern_occurrences=min_pattern_occurrences,
        )
        return result.to_dict()
