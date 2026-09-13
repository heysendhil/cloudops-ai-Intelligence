"""Log Analysis Task, executed by the Log Analyst Agent.

Per docs/agent-design.md task #1 (Log Analysis Task). Defines a strict,
structured expected output so the task's result is verifiable rather than
free text, and instructs the agent to ground every finding in the
log_analysis_tool's actual output -- no crew or flow is defined here.
"""

from __future__ import annotations

from crewai import Agent, Task
from pydantic import BaseModel, Field

from app.tools.log_analysis_tool import LogAnalysisTool

DEFAULT_INCIDENT_ID = "INC-2026-0912"
DEFAULT_START_TIME = "2026-09-12T13:50:00Z"
DEFAULT_END_TIME = "2026-09-12T14:45:00Z"


class LogAnalysisFinding(BaseModel):
    level: str = Field(description="Log level of the finding, e.g. ERROR or WARN.")
    line_number: int = Field(description="Line number in the source log file.")
    timestamp: str = Field(description="ISO 8601 timestamp of the log line.")
    raw_line: str = Field(description="The exact, verbatim raw log line -- never paraphrased.")
    description: str = Field(description="Short description of why this line matters.")


class RecurringLogPattern(BaseModel):
    description: str = Field(description="Description of the recurring message shape.")
    occurrences: int = Field(description="Number of times this pattern occurred.")
    line_numbers: list[int] = Field(description="Line numbers of every occurrence.")


class LogAnalysisReport(BaseModel):
    errors: list[LogAnalysisFinding] = Field(default_factory=list)
    warnings: list[LogAnalysisFinding] = Field(default_factory=list)
    recurring_patterns: list[RecurringLogPattern] = Field(default_factory=list)
    timestamps: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(
        default_factory=list,
        description="Exact raw log lines, verbatim from the source file, cited as evidence.",
    )
    summary: str = Field(description="Short prose summary of what the logs show.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence (0.0-1.0) that the log evidence alone supports the summary.",
    )


EXPECTED_OUTPUT = (
    "A structured log analysis report with exactly these fields: "
    "'errors' -- every ERROR-level finding, each with level, line_number, timestamp, "
    "raw_line, and a short description; "
    "'warnings' -- every WARN-level finding, same shape; "
    "'recurring_patterns' -- every repeated message pattern the tool reported, with its "
    "occurrence count and the line numbers of every occurrence; "
    "'timestamps' -- the sorted list of ISO 8601 timestamps covered by the evidence; "
    "'evidence' -- the exact raw log lines, verbatim from the source file, that support "
    "the findings; "
    "'summary' -- a short prose summary of what the logs show, citing only the evidence "
    "above; "
    "'confidence' -- a number between 0.0 and 1.0 reflecting how strongly the log "
    "evidence alone supports the summary. "
    "Every single field must be populated only from what the log_analysis_tool actually "
    "returned. A category with no findings must be reported as an empty list, never "
    "filled in with an invented or plausible-sounding entry."
)


def build_log_analysis_task(
    agent: Agent,
    log_path: str | None = None,
    start_time: str = DEFAULT_START_TIME,
    end_time: str = DEFAULT_END_TIME,
    incident_id: str = DEFAULT_INCIDENT_ID,
) -> Task:
    """Build the Log Analysis Task for the given (already-constructed) agent."""
    tool_args = f"start_time='{start_time}', end_time='{end_time}'"
    if log_path:
        tool_args += f", log_path='{log_path}'"

    description = (
        f"Investigate incident {incident_id} by analyzing its application log evidence. "
        f"Call the log_analysis_tool with {tool_args} to read the relevant log entries. "
        "Base every finding strictly on what the tool returns: use only the ERROR "
        "entries, WARN entries, repeated patterns, and timestamps the tool reports. "
        "Do not invent, infer, guess, or add any log line, error, warning, or pattern "
        "that the tool did not return, and do not alter the wording of a raw log line. "
        "If a category has no findings, report it as an empty list rather than "
        "fabricating a plausible-sounding entry."
    )

    return Task(
        description=description,
        expected_output=EXPECTED_OUTPUT,
        agent=agent,
        tools=[LogAnalysisTool()],
        output_pydantic=LogAnalysisReport,
    )
