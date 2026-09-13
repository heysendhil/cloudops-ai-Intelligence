"""Pure-Python log analysis core for the Log Analysis Tool.

No CrewAI, no LLM: this module only reads a log file from disk and extracts
structured facts from lines that are actually present in it. It never
synthesizes or paraphrases a log entry -- every returned item carries a line
number and the exact raw line it was read from, so results stay traceable
back to the source file.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOG_PATH = REPO_ROOT / "data" / "logs" / "payment-api.log"

# Matches lines like:
# payment-api-7f9c9d6b78-h5f7r 2026-09-12 13:50:02.011  INFO 1 --- [nio-8080-exec-2] c.p.controller.PaymentController : message
_LOG_LINE_PATTERN = re.compile(
    r"^(?P<pod>\S+)\s+"
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2}\.\d{3})\s+"
    r"(?P<level>INFO|WARN|ERROR|DEBUG)\s+"
    r"(?P<pid>\d+)\s+---\s+"
    r"\[(?P<thread>[^\]]*)\]\s+"
    r"(?P<logger>\S+)\s*:\s"
    r"(?P<message>.*)$"
)

# Substitutions applied before grouping messages into repeated patterns, so
# that only the variable parts (ids, durations, counters) are collapsed --
# the structural shape of the message (endpoint, logger, wording) is kept.
_PATTERN_NORMALIZATIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"duration_ms=\d+"), "duration_ms=<N>"),
    (re.compile(r"request_id=\S+"), "request_id=<ID>"),
    (re.compile(r"\bid=\S+"), "id=<ID>"),
    (re.compile(r"delta=\d+s\d+ms"), "delta=<N>"),
    (re.compile(r"\b\d+ms\b"), "<N>ms"),
    (re.compile(r"=\d+(\.\d+)?%"), "=<N>%"),
    (re.compile(r"\b\d+\b"), "<N>"),
)


def _normalize_message(message: str) -> str:
    normalized = message
    for pattern, replacement in _PATTERN_NORMALIZATIONS:
        normalized = pattern.sub(replacement, normalized)
    return normalized.strip()


def _coerce_datetime(value: datetime | str | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class LogEntry:
    """One parsed, timestamped log line. `line_number` + `raw_line` are the
    evidence reference back to the source file."""

    line_number: int
    timestamp: datetime
    pod: str
    level: str
    thread: str
    logger: str
    message: str
    raw_line: str

    def to_dict(self) -> dict:
        return {
            "line_number": self.line_number,
            "timestamp": self.timestamp.isoformat(),
            "pod": self.pod,
            "level": self.level,
            "thread": self.thread,
            "logger": self.logger,
            "message": self.message,
            "raw_line": self.raw_line,
        }


@dataclass(frozen=True)
class RepeatedPattern:
    """A normalized message shape that occurred more than once, with the
    exact line numbers of every occurrence as evidence."""

    level: str
    logger: str
    normalized_message: str
    occurrences: int
    line_numbers: list[int]
    example_raw_line: str

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "logger": self.logger,
            "normalized_message": self.normalized_message,
            "occurrences": self.occurrences,
            "line_numbers": self.line_numbers,
            "example_raw_line": self.example_raw_line,
        }


@dataclass(frozen=True)
class LogAnalysisResult:
    source_file: str
    window_start: datetime | None
    window_end: datetime | None
    total_lines_scanned: int
    total_entries_parsed: int
    entries_in_window: int
    error_entries: list[LogEntry]
    warn_entries: list[LogEntry]
    repeated_patterns: list[RepeatedPattern]
    timestamps: list[datetime]

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "window_end": self.window_end.isoformat() if self.window_end else None,
            "total_lines_scanned": self.total_lines_scanned,
            "total_entries_parsed": self.total_entries_parsed,
            "entries_in_window": self.entries_in_window,
            "error_entries": [e.to_dict() for e in self.error_entries],
            "warn_entries": [e.to_dict() for e in self.warn_entries],
            "repeated_patterns": [p.to_dict() for p in self.repeated_patterns],
            "timestamps": [t.isoformat() for t in self.timestamps],
        }


class LogAnalyzer:
    """Reads and analyzes a single log file. Stateless beyond the file path;
    safe to reuse across multiple `analyze()` calls with different windows.
    """

    def __init__(self, log_path: Path | str = DEFAULT_LOG_PATH) -> None:
        self.log_path = Path(log_path)

    def parse_entries(self) -> tuple[list[LogEntry], int]:
        """Parse every structured entry in the file.

        Returns:
            (entries, total_lines_scanned) -- total_lines_scanned counts every
            non-blank physical line read, whether or not it matched the
            structured entry format (e.g. stack trace continuation lines do
            not become entries but are still counted as scanned).
        """
        if not self.log_path.is_file():
            raise FileNotFoundError(f"Log file not found: {self.log_path}")

        entries: list[LogEntry] = []
        total_lines_scanned = 0

        with self.log_path.open(encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.rstrip("\n")
                if not line.strip():
                    continue
                total_lines_scanned += 1

                match = _LOG_LINE_PATTERN.match(line)
                if not match:
                    continue

                groups = match.groupdict()
                timestamp = datetime.strptime(
                    f"{groups['date']} {groups['time']}", "%Y-%m-%d %H:%M:%S.%f"
                ).replace(tzinfo=timezone.utc)

                entries.append(
                    LogEntry(
                        line_number=line_number,
                        timestamp=timestamp,
                        pod=groups["pod"],
                        level=groups["level"],
                        thread=groups["thread"],
                        logger=groups["logger"],
                        message=groups["message"],
                        raw_line=line,
                    )
                )

        return entries, total_lines_scanned

    def _find_repeated_patterns(
        self, entries: list[LogEntry], min_occurrences: int
    ) -> list[RepeatedPattern]:
        groups: dict[tuple[str, str, str], list[LogEntry]] = defaultdict(list)
        for entry in entries:
            key = (entry.level, entry.logger, _normalize_message(entry.message))
            groups[key].append(entry)

        patterns = [
            RepeatedPattern(
                level=level,
                logger=logger,
                normalized_message=normalized_message,
                occurrences=len(group_entries),
                line_numbers=[e.line_number for e in group_entries],
                example_raw_line=group_entries[0].raw_line,
            )
            for (level, logger, normalized_message), group_entries in groups.items()
            if len(group_entries) >= min_occurrences
        ]
        patterns.sort(key=lambda p: p.occurrences, reverse=True)
        return patterns

    def analyze(
        self,
        start_time: datetime | str | None = None,
        end_time: datetime | str | None = None,
        min_pattern_occurrences: int = 2,
    ) -> LogAnalysisResult:
        entries, total_lines_scanned = self.parse_entries()

        window_start = _coerce_datetime(start_time)
        window_end = _coerce_datetime(end_time)

        if window_start is not None or window_end is not None:
            filtered = [
                e
                for e in entries
                if (window_start is None or e.timestamp >= window_start)
                and (window_end is None or e.timestamp <= window_end)
            ]
        else:
            filtered = entries

        error_entries = [e for e in filtered if e.level == "ERROR"]
        warn_entries = [e for e in filtered if e.level == "WARN"]
        repeated_patterns = self._find_repeated_patterns(filtered, min_pattern_occurrences)
        timestamps = sorted({e.timestamp for e in filtered})

        return LogAnalysisResult(
            source_file=str(self.log_path),
            window_start=window_start,
            window_end=window_end,
            total_lines_scanned=total_lines_scanned,
            total_entries_parsed=len(entries),
            entries_in_window=len(filtered),
            error_entries=error_entries,
            warn_entries=warn_entries,
            repeated_patterns=repeated_patterns,
            timestamps=timestamps,
        )
