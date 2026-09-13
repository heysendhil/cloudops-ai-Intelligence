"""In-memory investigation job tracking for the visual investigation
workflow (Phase 20).

Per-agent status (Pending/Running/Completed/Failed) is sourced entirely
from CrewAI's own event bus (TaskStartedEvent / TaskCompletedEvent /
TaskFailedEvent), fired by the real Crew as it actually executes each
task -- nothing here is simulated. A task that the Flow never reaches
(e.g. the incident was invalid, so the Crew never ran) simply stays
"pending" forever; it is never marked complete without a real completion
event.

Each investigation runs in its own background thread (CloudOpsInvestigationFlow
.kickoff() is a long, blocking, multi-LLM-call operation) so the API layer
can start a job and let the caller poll it, instead of blocking the whole
HTTP request as app/api/incidents.py's original synchronous endpoint does
(that endpoint is unchanged and still works). A contextvar tracks which
job a given background thread's events belong to, so the (process-wide)
CrewAI event bus can route them to the right job even if two
investigations happen to run concurrently.
"""

from __future__ import annotations

import contextvars
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from crewai.events import crewai_event_bus
from crewai.events.types.task_events import (
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskStartedEvent,
)

from app.crew import CREW_TASK_NAMES
from app.flow import CloudOpsInvestigationFlow

TaskStatus = Literal["pending", "running", "completed", "failed"]
JobStatus = Literal["running", "succeeded", "failed", "invalid"]

_current_job_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_investigation_job_id", default=None
)


@dataclass
class TaskProgress:
    name: str
    status: TaskStatus = "pending"
    finding_summary: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "finding_summary": self.finding_summary,
            "error": self.error,
        }


@dataclass
class InvestigationJob:
    job_id: str
    incident_id: str
    status: JobStatus = "running"
    tasks: list[TaskProgress] = field(default_factory=list)
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "incident_id": self.incident_id,
            "status": self.status,
            "tasks": [t.to_dict() for t in self.tasks],
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
        }


_jobs: dict[str, InvestigationJob] = {}
_jobs_lock = threading.Lock()


def _task_display_name(task: Any) -> str | None:
    name = getattr(task, "name", None)
    return name if isinstance(name, str) and name else None


def _find_task(job: InvestigationJob, name: str) -> TaskProgress | None:
    for task_progress in job.tasks:
        if task_progress.name == name:
            return task_progress
    return None


def _summarize_output(output: Any) -> str | None:
    """Pull a short, real finding out of a TaskOutput -- never fabricated.
    Every task report schema has either a `summary` or (for the Root Cause
    and Incident Report tasks, which have no `summary` field) a
    `root_cause` field; falls back to the raw text if neither is present.
    """
    pydantic_result = getattr(output, "pydantic", None)
    if pydantic_result is not None:
        for field_name in ("summary", "root_cause"):
            value = getattr(pydantic_result, field_name, None)
            if isinstance(value, str) and value.strip():
                return value
    raw = getattr(output, "raw", None)
    if isinstance(raw, str) and raw.strip():
        return raw[:280] + ("..." if len(raw) > 280 else "")
    return None


@crewai_event_bus.on(TaskStartedEvent)
def _on_task_started(source: Any, event: TaskStartedEvent) -> None:
    job_id = _current_job_id.get()
    if job_id is None:
        return
    name = _task_display_name(event.task)
    if name is None:
        return

    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        task_progress = _find_task(job, name)
        if task_progress is None:
            task_progress = TaskProgress(name=name)
            job.tasks.append(task_progress)
        task_progress.status = "running"


@crewai_event_bus.on(TaskCompletedEvent)
def _on_task_completed(source: Any, event: TaskCompletedEvent) -> None:
    job_id = _current_job_id.get()
    if job_id is None:
        return
    name = _task_display_name(event.task)
    if name is None:
        return

    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        task_progress = _find_task(job, name)
        if task_progress is None:
            task_progress = TaskProgress(name=name)
            job.tasks.append(task_progress)
        task_progress.status = "completed"
        task_progress.finding_summary = _summarize_output(event.output)


@crewai_event_bus.on(TaskFailedEvent)
def _on_task_failed(source: Any, event: TaskFailedEvent) -> None:
    job_id = _current_job_id.get()
    if job_id is None:
        return
    name = _task_display_name(event.task)
    if name is None:
        return

    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        task_progress = _find_task(job, name)
        if task_progress is None:
            task_progress = TaskProgress(name=name)
            job.tasks.append(task_progress)
        task_progress.status = "failed"
        task_progress.error = event.error


def start_investigation(incident_id: str) -> InvestigationJob:
    """Start a new investigation in a background thread and return its
    (initially all-pending) job immediately. Poll get_job(job_id) for
    progress; nothing here blocks the caller.
    """
    job = InvestigationJob(
        job_id=str(uuid.uuid4()),
        incident_id=incident_id,
        tasks=[TaskProgress(name=name) for name in CREW_TASK_NAMES],
    )
    with _jobs_lock:
        _jobs[job.job_id] = job

    def _run() -> None:
        token = _current_job_id.set(job.job_id)
        try:
            flow = CloudOpsInvestigationFlow()
            result = flow.kickoff(inputs={"incident_id": incident_id})
            with _jobs_lock:
                job.result = result
                job.status = result.get("status", "failed")
                job.error = result.get("error")
        except Exception as exc:  # noqa: BLE001 -- captured for polling, not raised
            with _jobs_lock:
                job.status = "failed"
                job.error = f"{type(exc).__name__}: {exc}"
        finally:
            _current_job_id.reset(token)

    threading.Thread(target=_run, daemon=True).start()
    return job


def get_job(job_id: str) -> InvestigationJob | None:
    with _jobs_lock:
        return _jobs.get(job_id)
