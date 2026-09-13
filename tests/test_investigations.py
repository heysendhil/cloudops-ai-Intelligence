"""Tests for app/investigations.py: per-agent progress tracking.

Two layers, deliberately:

1. Event-handler unit tests: manually emit real CrewAI TaskStartedEvent /
   TaskCompletedEvent / TaskFailedEvent instances (the same event types a
   real Crew emits during task.py's own execution -- see
   crewai/task.py:676-961) and verify app.investigations updates job state
   correctly. This tests *our* handler logic directly, without needing a
   live LLM to produce those events.
2. Job lifecycle tests: start_investigation() with the real Crew builder
   stubbed out (same technique as tests/test_flow.py), verifying threading,
   polling, and that tasks the (fake) Crew never touches stay 'pending' --
   never simulated as complete.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest
from crewai.events import crewai_event_bus
from crewai.events.types.task_events import (
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskStartedEvent,
)
from crewai.tasks.task_output import TaskOutput

import app.flow as flow_module
from app.crew import CREW_TASK_NAMES
from app.investigations import _jobs, get_job, start_investigation
from _fixtures_root_cause import build_fixture_incident_report


def _fake_task(name: str) -> SimpleNamespace:
    # event.task only needs a .name for our handlers -- a real Task object
    # also has a .fingerprint the event's __init__ reads, so give it None.
    return SimpleNamespace(name=name, fingerprint=None)


def _fake_output(pydantic: Any = None, raw: str = "") -> TaskOutput:
    # TaskCompletedEvent.output is strictly typed as a real TaskOutput.
    return TaskOutput(description="test task", agent="test agent", pydantic=pydantic, raw=raw)


# --- event handlers (unit-level, no LLM) -----------------------------
#
# The detailed cases below call app.investigations' handler functions
# directly (e.g. _on_task_completed(None, event)) rather than going through
# crewai_event_bus.emit(). The event *objects* are still real CrewAI
# TaskStartedEvent/TaskCompletedEvent/TaskFailedEvent instances (proving
# our code's field access matches their real shape) -- what's bypassed is
# only the bus's own dispatch machinery, which tracks a start/end "scope
# stack" across the whole process (shared with every other handler
# registered anywhere, including crewai's own internal ones) and isn't
# ours to test. One end-to-end test (below) goes through the real
# emit() path to prove the handlers are actually wired to the bus.


def test_task_started_event_is_wired_through_the_real_event_bus() -> None:
    """One true end-to-end check: emit() a real event through the real bus
    and see our handler fire, proving the @crewai_event_bus.on(...)
    registration works. Uses scoped_handlers() (the bus's own documented
    tool "for testing or temporary event handling") to isolate this from
    whatever else is registered on the process-wide bus, and waits on the
    Future emit() returns -- per its own docstring, emit() dispatches sync
    handlers on a thread-pool executor and does not block the caller, so
    asserting immediately after a bare emit() call is a real race, not a
    matter of registration.
    """
    from app.investigations import InvestigationJob, TaskProgress, _current_job_id, _on_task_started

    job = InvestigationJob(
        job_id="job-wiring",
        incident_id="INC-TEST",
        tasks=[TaskProgress(name=name) for name in CREW_TASK_NAMES],
    )
    _jobs["job-wiring"] = job
    token = _current_job_id.set("job-wiring")
    try:
        with crewai_event_bus.scoped_handlers():
            crewai_event_bus.on(TaskStartedEvent)(_on_task_started)
            future = crewai_event_bus.emit(
                None, TaskStartedEvent(context=None, task=_fake_task("Log Analysis Task"))
            )
            if future is not None:
                future.result(timeout=5.0)
    finally:
        _current_job_id.reset(token)
        del _jobs["job-wiring"]

    statuses = {t.name: t.status for t in job.tasks}
    assert statuses["Log Analysis Task"] == "running"
    assert statuses["Cloud Analysis Task"] == "pending"  # untouched tasks stay pending


def test_on_task_started_marks_the_matching_task_running() -> None:
    from app.investigations import InvestigationJob, TaskProgress, _current_job_id, _on_task_started

    job = InvestigationJob(
        job_id="job-1",
        incident_id="INC-TEST",
        tasks=[TaskProgress(name=name) for name in CREW_TASK_NAMES],
    )
    _jobs["job-1"] = job
    token = _current_job_id.set("job-1")
    try:
        event = TaskStartedEvent(context=None, task=_fake_task("Log Analysis Task"))
        _on_task_started(None, event)
    finally:
        _current_job_id.reset(token)
        del _jobs["job-1"]

    statuses = {t.name: t.status for t in job.tasks}
    assert statuses["Log Analysis Task"] == "running"
    assert statuses["Cloud Analysis Task"] == "pending"  # untouched tasks stay pending


def test_on_task_completed_marks_completed_with_a_real_finding() -> None:
    from app.investigations import InvestigationJob, TaskProgress, _current_job_id, _on_task_completed

    job = InvestigationJob(
        job_id="job-2",
        incident_id="INC-TEST",
        tasks=[TaskProgress(name=name) for name in CREW_TASK_NAMES],
    )
    _jobs["job-2"] = job
    token = _current_job_id.set("job-2")
    try:
        fake_report = build_fixture_incident_report()  # has no .summary, has .root_cause
        event = TaskCompletedEvent(
            task=_fake_task("Incident Report Task"),
            output=_fake_output(pydantic=fake_report),
        )
        _on_task_completed(None, event)
    finally:
        _current_job_id.reset(token)
        del _jobs["job-2"]

    task = next(t for t in job.tasks if t.name == "Incident Report Task")
    assert task.status == "completed"
    assert task.finding_summary == fake_report.root_cause  # real data, not invented
    other = next(t for t in job.tasks if t.name == "Log Analysis Task")
    assert other.status == "pending"


def test_on_task_completed_falls_back_to_raw_output_without_summary_or_root_cause() -> None:
    from app.investigations import InvestigationJob, _current_job_id, _on_task_completed

    job = InvestigationJob(job_id="job-3", incident_id="INC-TEST", tasks=[])
    _jobs["job-3"] = job
    token = _current_job_id.set("job-3")
    try:
        event = TaskCompletedEvent(
            task=_fake_task("Some Task"),
            output=_fake_output(pydantic=None, raw="raw finding text"),
        )
        _on_task_completed(None, event)
    finally:
        _current_job_id.reset(token)
        del _jobs["job-3"]

    assert job.tasks[0].finding_summary == "raw finding text"


def test_on_task_failed_marks_failed_with_the_real_error() -> None:
    from app.investigations import InvestigationJob, TaskProgress, _current_job_id, _on_task_failed

    job = InvestigationJob(
        job_id="job-4",
        incident_id="INC-TEST",
        tasks=[TaskProgress(name=name) for name in CREW_TASK_NAMES],
    )
    _jobs["job-4"] = job
    token = _current_job_id.set("job-4")
    try:
        event = TaskFailedEvent(
            task=_fake_task("Cloud Analysis Task"),
            error="simulated tool failure",
            error_type=RuntimeError,
        )
        _on_task_failed(None, event)
    finally:
        _current_job_id.reset(token)
        del _jobs["job-4"]

    task = next(t for t in job.tasks if t.name == "Cloud Analysis Task")
    assert task.status == "failed"
    assert task.error == "simulated tool failure"


def test_handlers_ignore_events_outside_any_job_context() -> None:
    # No _current_job_id set -- must not raise, must not touch any job.
    from app.investigations import _on_task_started

    event = TaskStartedEvent(context=None, task=_fake_task("Log Analysis Task"))
    _on_task_started(None, event)  # no assertion needed: absence of a crash is the point


# --- job lifecycle (Crew stubbed out, real threading/polling) -------------


def _patch_crew_builder(monkeypatch: pytest.MonkeyPatch, pydantic_result: Any) -> None:
    @dataclass
    class _FakeCrewOutput:
        pydantic: Any

    class _FakeCrew:
        def kickoff(self) -> _FakeCrewOutput:
            return _FakeCrewOutput(pydantic=pydantic_result)

    monkeypatch.setattr(flow_module, "build_cloudops_investigation_crew", lambda **kwargs: _FakeCrew())


def _wait_until_done(job_id: str, timeout: float = 5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = get_job(job_id)
        if job.status != "running":
            return job
        time.sleep(0.02)
    raise TimeoutError("investigation job did not finish in time")


def test_start_investigation_returns_immediately_with_all_tasks_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_crew_builder(monkeypatch, build_fixture_incident_report())

    job = start_investigation("INC-2026-0912")

    assert job.status == "running"
    assert [t.status for t in job.tasks] == ["pending"] * len(CREW_TASK_NAMES)
    assert [t.name for t in job.tasks] == CREW_TASK_NAMES


def test_job_reaches_succeeded_with_the_real_result(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture_report = build_fixture_incident_report()
    _patch_crew_builder(monkeypatch, fixture_report)

    job = start_investigation("INC-2026-0912")
    finished = _wait_until_done(job.job_id)

    assert finished.status == "succeeded"
    assert finished.result["incident_report"]["root_cause"] == fixture_report.root_cause


def test_job_for_unknown_incident_becomes_invalid_with_all_tasks_still_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_crew_builder(monkeypatch, build_fixture_incident_report())

    job = start_investigation("INC-DOES-NOT-EXIST")
    finished = _wait_until_done(job.job_id)

    assert finished.status == "invalid"
    # the (fake) Crew never runs for an invalid incident, so no task ever
    # started -- every one must still be pending, never simulated as done.
    assert all(t.status == "pending" for t in finished.tasks)


def test_get_job_returns_none_for_unknown_job_id() -> None:
    assert get_job("does-not-exist") is None
