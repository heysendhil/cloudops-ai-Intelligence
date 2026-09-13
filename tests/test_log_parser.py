from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.tools.log_parser import LogAnalyzer

FIXTURE_LOG = """\
app-pod-1 2026-01-01 09:00:00.000  INFO 1 --- [main] com.example.App : Outside window entry
app-pod-1 2026-01-01 10:00:00.000  INFO 1 --- [main] com.example.App : Started application
app-pod-1 2026-01-01 10:01:00.000  WARN 1 --- [exec-1] com.example.Db : Slow query detected duration_ms=500
app-pod-1 2026-01-01 10:02:00.000  WARN 1 --- [exec-1] com.example.Db : Slow query detected duration_ms=900
app-pod-2 2026-01-01 10:03:00.000 ERROR 1 --- [exec-2] com.example.Handler : Request failed request_id=req_1
app-pod-2 2026-01-01 10:04:00.000 ERROR 1 --- [exec-2] com.example.Handler : Request failed request_id=req_2
app-pod-2 2026-01-01 10:04:30.000 ERROR 1 --- [exec-2] com.example.Handler : Request failed request_id=req_3
app-pod-1 2026-01-01 10:05:00.000  INFO 1 --- [main] com.example.App : Shutting down
java.lang.RuntimeException: boom
\tat com.example.Foo.bar(Foo.java:10)
"""


@pytest.fixture()
def fixture_log_path(tmp_path: Path) -> Path:
    log_file = tmp_path / "fixture.log"
    log_file.write_text(FIXTURE_LOG)
    return log_file


def test_parse_entries_extracts_structured_fields(fixture_log_path: Path) -> None:
    analyzer = LogAnalyzer(fixture_log_path)

    entries, total_lines_scanned = analyzer.parse_entries()

    assert total_lines_scanned == 10  # 8 log lines + exception line + stack frame
    assert len(entries) == 8  # the exception/stack-frame lines are not entries

    first = entries[0]
    assert first.line_number == 1
    assert first.pod == "app-pod-1"
    assert first.level == "INFO"
    assert first.logger == "com.example.App"
    assert first.message == "Outside window entry"
    assert first.timestamp == datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)


def test_raw_line_is_exact_evidence_reference(fixture_log_path: Path) -> None:
    analyzer = LogAnalyzer(fixture_log_path)
    entries, _ = analyzer.parse_entries()

    original_lines = FIXTURE_LOG.splitlines()
    for entry in entries:
        assert entry.raw_line == original_lines[entry.line_number - 1]


def test_identifies_error_entries(fixture_log_path: Path) -> None:
    result = LogAnalyzer(fixture_log_path).analyze()

    assert len(result.error_entries) == 3
    assert all(e.level == "ERROR" for e in result.error_entries)
    assert all(e.logger == "com.example.Handler" for e in result.error_entries)


def test_identifies_warn_entries(fixture_log_path: Path) -> None:
    result = LogAnalyzer(fixture_log_path).analyze()

    assert len(result.warn_entries) == 2
    assert all(e.level == "WARN" for e in result.warn_entries)


def test_filters_to_incident_timeframe(fixture_log_path: Path) -> None:
    result = LogAnalyzer(fixture_log_path).analyze(
        start_time="2026-01-01T09:30:00Z",
        end_time="2026-01-01T10:10:00Z",
    )

    assert result.entries_in_window == 7  # excludes the 09:00 "outside window" entry
    assert result.total_entries_parsed == 8  # parsing itself is not window-limited
    assert all(t >= datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc) for t in result.timestamps)


def test_identifies_repeated_patterns_with_normalization(fixture_log_path: Path) -> None:
    result = LogAnalyzer(fixture_log_path).analyze(min_pattern_occurrences=2)

    assert len(result.repeated_patterns) == 2
    top = result.repeated_patterns[0]
    assert top.occurrences == 3
    assert top.level == "ERROR"
    assert top.logger == "com.example.Handler"
    assert "request_id=<ID>" in top.normalized_message
    assert top.line_numbers == [5, 6, 7]

    second = result.repeated_patterns[1]
    assert second.occurrences == 2
    assert second.level == "WARN"
    assert "duration_ms=<N>" in second.normalized_message


def test_min_pattern_occurrences_threshold_is_respected(fixture_log_path: Path) -> None:
    result = LogAnalyzer(fixture_log_path).analyze(min_pattern_occurrences=3)

    assert len(result.repeated_patterns) == 1
    assert result.repeated_patterns[0].occurrences == 3


def test_extracts_sorted_unique_timestamps(fixture_log_path: Path) -> None:
    result = LogAnalyzer(fixture_log_path).analyze()

    assert result.timestamps == sorted(result.timestamps)
    assert len(result.timestamps) == len(set(result.timestamps))


def test_never_invents_entries_not_present_in_file(fixture_log_path: Path) -> None:
    result = LogAnalyzer(fixture_log_path).analyze()

    for entry in result.error_entries + result.warn_entries:
        assert entry.raw_line in FIXTURE_LOG
    for pattern in result.repeated_patterns:
        assert pattern.example_raw_line in FIXTURE_LOG
    # nothing in the exception/stack-trace lines should surface as an entry
    assert not any("RuntimeException" in e.message for e in result.error_entries)


def test_missing_log_file_raises_file_not_found(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist.log"

    with pytest.raises(FileNotFoundError):
        LogAnalyzer(missing_path).parse_entries()


def test_empty_log_file_yields_no_entries_not_fabricated_ones(tmp_path: Path) -> None:
    empty_log = tmp_path / "empty.log"
    empty_log.write_text("")

    result = LogAnalyzer(empty_log).analyze()

    assert result.total_entries_parsed == 0
    assert result.error_entries == []
    assert result.warn_entries == []
    assert result.repeated_patterns == []
    assert result.timestamps == []


def test_result_to_dict_is_json_serializable(fixture_log_path: Path) -> None:
    import json

    result = LogAnalyzer(fixture_log_path).analyze()

    serialized = json.dumps(result.to_dict())
    assert "error_entries" in serialized
    assert "warn_entries" in serialized
    assert "repeated_patterns" in serialized
