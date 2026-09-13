"""Golden-scenario evaluation for the Log Analyst Agent against the real
INC-2026-0912 incident log (see docs/evaluation.md).

This exercises a real LLM call via the Log Analyst Agent + Log Analysis
Task (no Crew involved -- Task.execute_sync runs a single task against a
single agent). It requires a real GOOGLE_API_KEY and is skipped gracefully
without one, per the project's "handle missing API keys gracefully" rule.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.agents.log_analyst import build_log_analyst_agent
from app.llm_config import is_configured
from app.tasks.log_analysis_task import (
    DEFAULT_END_TIME,
    DEFAULT_START_TIME,
    LogAnalysisReport,
    build_log_analysis_task,
)
from app.tools.log_analysis_tool import LogAnalysisTool

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = REPO_ROOT / "data" / "logs" / "payment-api.log"

pytestmark = [
    pytest.mark.live_llm,
    pytest.mark.skipif(
        not is_configured(),
        reason=(
            "GOOGLE_API_KEY is not set -- skipping live Log Analyst evaluation. "
            "Set it in backend/.env to run this evaluation against a real model."
        ),
    ),
]


@pytest.fixture(scope="module")
def evaluation_result() -> LogAnalysisReport:
    agent = build_log_analyst_agent()
    task = build_log_analysis_task(agent)
    output = task.execute_sync(agent=agent)

    assert output.pydantic is not None, "Task did not produce structured output"
    return output.pydantic


@pytest.fixture(scope="module")
def ground_truth() -> dict:
    # The tool's own direct output is the ground truth the agent must match.
    tool = LogAnalysisTool()
    return tool.run(start_time=DEFAULT_START_TIME, end_time=DEFAULT_END_TIME)


def test_agent_finds_at_least_one_error(evaluation_result: LogAnalysisReport) -> None:
    assert len(evaluation_result.errors) > 0


def test_agent_finds_at_least_one_warning(evaluation_result: LogAnalysisReport) -> None:
    assert len(evaluation_result.warnings) > 0


def test_agent_identifies_recurring_patterns(evaluation_result: LogAnalysisReport) -> None:
    assert len(evaluation_result.recurring_patterns) > 0


def test_agent_extracts_timestamps(evaluation_result: LogAnalysisReport) -> None:
    assert len(evaluation_result.timestamps) > 0


def test_agent_reports_confidence_in_valid_range(evaluation_result: LogAnalysisReport) -> None:
    assert 0.0 <= evaluation_result.confidence <= 1.0


def test_agent_summary_is_non_empty(evaluation_result: LogAnalysisReport) -> None:
    assert evaluation_result.summary.strip() != ""


def test_agent_never_invents_evidence(evaluation_result: LogAnalysisReport) -> None:
    log_text = LOG_PATH.read_text()

    for line in evaluation_result.evidence:
        assert line in log_text, f"Evidence line not found verbatim in source log: {line!r}"
    for finding in evaluation_result.errors + evaluation_result.warnings:
        assert finding.raw_line in log_text, f"Finding not grounded in source log: {finding!r}"


def test_agent_error_findings_match_tool_ground_truth_exactly(
    evaluation_result: LogAnalysisReport, ground_truth: dict
) -> None:
    reported = {f.raw_line for f in evaluation_result.errors}
    expected = {e["raw_line"] for e in ground_truth["error_entries"]}
    assert reported == expected


def test_agent_warning_findings_match_tool_ground_truth_exactly(
    evaluation_result: LogAnalysisReport, ground_truth: dict
) -> None:
    reported = {f.raw_line for f in evaluation_result.warnings}
    expected = {e["raw_line"] for e in ground_truth["warn_entries"]}
    assert reported == expected
