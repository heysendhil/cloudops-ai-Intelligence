"""Tests for the CloudOps Incident Investigation Flow.

Runs entirely offline: the CloudOps Investigation Crew is a real,
expensive, multi-LLM-call dependency (see app/crew.py), so these tests
monkeypatch app.flow.build_cloudops_investigation_crew with a stub crew
whose .kickoff() returns canned CrewOutput-like results. This still
exercises the Flow's *real* logic (validation, data loading from the real
data/incidents/INC-2026-0912.json, routing, failure handling, and result
assembly) end-to-end via a real .kickoff() call -- only the Crew's own
(separately and extensively tested, see tests/test_crew.py and
tests/evaluation/) execution is stubbed out here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.flow import CloudOpsInvestigationFlow, InvestigationStatus
from _fixtures_root_cause import build_fixture_incident_report

import app.flow as flow_module


@dataclass
class _FakeCrewOutput:
    pydantic: Any


class _FakeCrew:
    def __init__(self, pydantic_result: Any, raise_exc: Exception | None = None) -> None:
        self._pydantic_result = pydantic_result
        self._raise_exc = raise_exc

    def kickoff(self) -> _FakeCrewOutput:
        if self._raise_exc is not None:
            raise self._raise_exc
        return _FakeCrewOutput(pydantic=self._pydantic_result)


def _patch_crew_builder(
    monkeypatch: pytest.MonkeyPatch, pydantic_result: Any = None, raise_exc: Exception | None = None
) -> list[dict]:
    """Patches the crew builder used inside the Flow and returns a list that
    records every call's kwargs, so tests can assert the Flow invoked the
    Crew with the right incident data (or didn't invoke it at all)."""
    calls: list[dict] = []

    def _fake_builder(**kwargs: Any) -> _FakeCrew:
        calls.append(kwargs)
        return _FakeCrew(pydantic_result, raise_exc=raise_exc)

    monkeypatch.setattr(flow_module, "build_cloudops_investigation_crew", _fake_builder)
    return calls


# --- full end-to-end run against the real INC-2026-0912 data --------------


def test_successful_investigation_against_inc_2026_0912(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture_report = build_fixture_incident_report()
    _patch_crew_builder(monkeypatch, pydantic_result=fixture_report)

    flow = CloudOpsInvestigationFlow()
    result = flow.kickoff(inputs={"incident_id": "INC-2026-0912"})

    assert result["status"] == "succeeded"
    assert result["error"] is None
    assert result["incident_id"] == "INC-2026-0912"
    assert result["incident_report"]["root_cause"] == fixture_report.root_cause
    assert result["requires_human_approval"] is True


def test_real_incident_data_is_loaded_from_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture_report = build_fixture_incident_report()
    calls = _patch_crew_builder(monkeypatch, pydantic_result=fixture_report)

    flow = CloudOpsInvestigationFlow()
    flow.kickoff(inputs={"incident_id": "INC-2026-0912"})

    # The Flow must have loaded the real incident record and passed it to
    # the Crew -- not invented or hardcoded elsewhere.
    assert len(calls) == 1
    assert calls[0]["incident_id"] == "INC-2026-0912"
    assert calls[0]["severity"] == "SEV-2"
    assert calls[0]["service"] == "Payment API"
    assert "elevated latency" in calls[0]["impact"]


def test_final_state_matches_the_returned_result(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture_report = build_fixture_incident_report()
    _patch_crew_builder(monkeypatch, pydantic_result=fixture_report)

    flow = CloudOpsInvestigationFlow()
    result = flow.kickoff(inputs={"incident_id": "INC-2026-0912"})

    assert flow.state.status == InvestigationStatus.SUCCEEDED
    assert flow.state.incident_report == result["incident_report"]


# --- validation failure: crew must never be invoked -------------------


def test_missing_incident_id_fails_validation_without_invoking_crew(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _patch_crew_builder(monkeypatch, pydantic_result=build_fixture_incident_report())

    flow = CloudOpsInvestigationFlow()
    result = flow.kickoff(inputs={"incident_id": ""})

    assert result["status"] == "invalid"
    assert result["error"] is not None
    assert result["incident_report"] is None
    assert calls == []  # the Crew must never run for an invalid incident


def test_unknown_incident_id_fails_validation_without_invoking_crew(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _patch_crew_builder(monkeypatch, pydantic_result=build_fixture_incident_report())

    flow = CloudOpsInvestigationFlow()
    result = flow.kickoff(inputs={"incident_id": "INC-DOES-NOT-EXIST"})

    assert result["status"] == "invalid"
    assert "INC-DOES-NOT-EXIST" in result["error"]
    assert calls == []


# --- crew-level failure handling ----------------------------------------


def test_crew_raising_an_exception_is_handled_not_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_crew_builder(monkeypatch, raise_exc=RuntimeError("simulated LLM outage"))

    flow = CloudOpsInvestigationFlow()
    result = flow.kickoff(inputs={"incident_id": "INC-2026-0912"})

    assert result["status"] == "failed"
    assert "simulated LLM outage" in result["error"]
    assert result["incident_report"] is None
    assert result["requires_human_approval"] is True


def test_crew_returning_no_structured_output_is_handled(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_crew_builder(monkeypatch, pydantic_result=None)

    flow = CloudOpsInvestigationFlow()
    result = flow.kickoff(inputs={"incident_id": "INC-2026-0912"})

    assert result["status"] == "failed"
    assert "no structured incident report" in result["error"].lower()


def test_crew_returning_incomplete_report_is_caught_by_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    incomplete = build_fixture_incident_report().model_copy(update={"root_cause": ""})
    _patch_crew_builder(monkeypatch, pydantic_result=incomplete)

    flow = CloudOpsInvestigationFlow()
    result = flow.kickoff(inputs={"incident_id": "INC-2026-0912"})

    assert result["status"] == "failed"
    assert "root_cause" in result["error"]


# --- safety: the flow never executes anything, always requires approval ---


def test_result_always_states_human_approval_is_required_even_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_crew_builder(monkeypatch, raise_exc=RuntimeError("boom"))

    flow = CloudOpsInvestigationFlow()
    result = flow.kickoff(inputs={"incident_id": "INC-2026-0912"})

    assert result["requires_human_approval"] is True


def test_flow_module_has_no_remediation_execution_capability() -> None:
    import inspect

    source = inspect.getsource(flow_module)
    for forbidden in ("subprocess", "os.system", "kubectl", "boto3", "requests.post"):
        assert forbidden not in source


# --- individual method behavior (direct calls, no event system) -----------


def test_validate_incident_router_returns_valid_for_known_incident() -> None:
    flow = CloudOpsInvestigationFlow()
    flow.state.incident_id = "INC-2026-0912"

    assert flow.validate_incident() == "valid"
    assert flow.state.status == InvestigationStatus.VALIDATED


def test_validate_incident_router_returns_invalid_for_unknown_incident() -> None:
    flow = CloudOpsInvestigationFlow()
    flow.state.incident_id = "INC-NOPE"

    assert flow.validate_incident() == "invalid"
    assert flow.state.status == InvestigationStatus.INVALID
    assert flow.state.error is not None


def test_load_incident_data_populates_state_from_the_real_record() -> None:
    flow = CloudOpsInvestigationFlow()
    flow.state.incident_id = "INC-2026-0912"

    flow.load_incident_data()

    assert flow.state.severity == "SEV-2"
    assert flow.state.service == "Payment API"
    assert flow.state.status == InvestigationStatus.LOADED
