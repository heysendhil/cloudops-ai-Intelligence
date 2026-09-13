from pathlib import Path

import pytest
from crewai.tools import BaseTool

from app.tools.log_analysis_tool import LogAnalysisTool

FIXTURE_LOG = """\
app-pod-1 2026-01-01 10:00:00.000  INFO 1 --- [main] com.example.App : Started application
app-pod-2 2026-01-01 10:01:00.000 ERROR 1 --- [exec-2] com.example.Handler : Request failed request_id=req_1
app-pod-2 2026-01-01 10:02:00.000 ERROR 1 --- [exec-2] com.example.Handler : Request failed request_id=req_2
"""


@pytest.fixture()
def fixture_log_path(tmp_path: Path) -> Path:
    log_file = tmp_path / "fixture.log"
    log_file.write_text(FIXTURE_LOG)
    return log_file


def test_tool_is_a_crewai_basetool() -> None:
    tool = LogAnalysisTool()

    assert isinstance(tool, BaseTool)
    assert tool.name == "log_analysis_tool"
    assert "log" in tool.description.lower()


def test_tool_run_returns_expected_structure(fixture_log_path: Path) -> None:
    tool = LogAnalysisTool()

    output = tool.run(log_path=str(fixture_log_path))

    assert output["total_entries_parsed"] == 3
    assert len(output["error_entries"]) == 2
    assert output["error_entries"][0]["level"] == "ERROR"
    assert output["error_entries"][0]["raw_line"] in FIXTURE_LOG


def test_tool_run_works_without_any_llm_configured(
    fixture_log_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # No GOOGLE_API_KEY, no LLM client anywhere in this call path -- the tool
    # must work purely from local file parsing.
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    tool = LogAnalysisTool()

    output = tool.run(log_path=str(fixture_log_path))

    assert output["total_entries_parsed"] == 3


def test_tool_run_applies_time_window_and_min_occurrences(fixture_log_path: Path) -> None:
    tool = LogAnalysisTool()

    output = tool.run(
        log_path=str(fixture_log_path),
        start_time="2026-01-01T10:00:30Z",
        end_time="2026-01-01T10:10:00Z",
        min_pattern_occurrences=2,
    )

    assert output["entries_in_window"] == 2  # excludes the 10:00:00 INFO line
    assert len(output["repeated_patterns"]) == 1
    assert output["repeated_patterns"][0]["occurrences"] == 2


def test_tool_default_log_path_reads_the_real_incident_log() -> None:
    tool = LogAnalysisTool()

    output = tool.run(
        start_time="2026-09-12T13:50:00Z",
        end_time="2026-09-12T14:45:00Z",
    )

    assert output["total_entries_parsed"] > 0
    assert len(output["error_entries"]) > 0
    assert len(output["warn_entries"]) > 0
    assert any(
        "HikariPool" in e["raw_line"] or "HikariPool" in e["message"]
        for e in output["warn_entries"]
    )
    # every finding must be traceable to a real line in the actual log file
    log_text = Path(output["source_file"]).read_text()
    for entry in output["error_entries"] + output["warn_entries"]:
        assert entry["raw_line"] in log_text
