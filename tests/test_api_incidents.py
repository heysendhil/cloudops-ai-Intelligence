"""Integration tests for POST /incidents/{incident_id}/investigate.

Runs entirely offline: app.api.incidents.CloudOpsInvestigationFlow's
underlying Crew invocation is monkeypatched the same way
tests/test_flow.py does it (via app.flow.build_cloudops_investigation_crew),
so these exercise the real FastAPI request/response cycle, real path
validation, and the real Flow logic end-to-end, without needing a live LLM.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.flow as flow_module
from app.main import app
from _fixtures_root_cause import build_fixture_incident_report


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
) -> None:
    monkeypatch.setattr(
        flow_module,
        "build_cloudops_investigation_crew",
        lambda **kwargs: _FakeCrew(pydantic_result, raise_exc=raise_exc),
    )


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# --- GET incident summary (read-only, no investigation) --------------------


def test_get_incident_summary_returns_real_incident_metadata(client: TestClient) -> None:
    response = client.get("/incidents/INC-2026-0912")

    assert response.status_code == 200
    body = response.json()
    assert body["incident_id"] == "INC-2026-0912"
    assert body["severity"] == "SEV-2"
    assert body["service"] == "Payment API"
    assert body["environment"] == "production"
    assert body["platform"] == "Kubernetes on AWS"
    assert len(body["symptoms"]) >= 4


def test_get_incident_summary_unknown_incident_returns_404(client: TestClient) -> None:
    response = client.get("/incidents/INC-DOES-NOT-EXIST")

    assert response.status_code == 404


def test_get_incident_summary_malformed_id_returns_422(client: TestClient) -> None:
    response = client.get("/incidents/INC 2026 0912")

    assert response.status_code == 422


# --- success path -----------------------------------------------------


def test_successful_investigation_returns_200_with_full_report(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture_report = build_fixture_incident_report()
    _patch_crew_builder(monkeypatch, pydantic_result=fixture_report)

    response = client.post("/incidents/INC-2026-0912/investigate")

    assert response.status_code == 200
    body = response.json()
    assert body["incident_id"] == "INC-2026-0912"
    assert body["status"] == "succeeded"
    assert body["error"] is None
    assert body["incident_report"]["root_cause"] == fixture_report.root_cause
    assert body["requires_human_approval"] is True


def test_successful_investigation_report_includes_all_required_sections(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_crew_builder(monkeypatch, pydantic_result=build_fixture_incident_report())

    response = client.post("/incidents/INC-2026-0912/investigate")

    report = response.json()["incident_report"]
    for field in (
        "incident_id",
        "severity",
        "service",
        "impact",
        "timeline",
        "log_findings",
        "cloud_findings",
        "kubernetes_findings",
        "relevant_runbook",
        "root_cause",
        "alternative_hypotheses",
        "confidence",
        "remediation_recommendations",
        "human_approval_requirement",
    ):
        assert field in report


# --- request validation -------------------------------------------------


@pytest.mark.parametrize(
    "bad_incident_id",
    [
        "INC 2026 0912",  # space -- a valid single path segment (URL-encoded), fails our pattern
        "INC-2026-0912!!!",  # disallowed punctuation, still a single path segment
    ],
)
def test_malformed_incident_id_returns_422(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, bad_incident_id: str
) -> None:
    """Values that are a single path segment but violate the allowed
    character set are rejected by Path(pattern=...) validation -> 422."""
    _patch_crew_builder(monkeypatch, pydantic_result=build_fixture_incident_report())

    response = client.post(f"/incidents/{bad_incident_id}/investigate")

    assert response.status_code == 422


@pytest.mark.parametrize(
    "bad_incident_id",
    [
        "../../etc/passwd",
        "INC/2026/0912",
    ],
)
def test_incident_id_containing_a_path_separator_never_reaches_the_handler(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, bad_incident_id: str
) -> None:
    """A value containing '/' does not match the single {incident_id} path
    segment at all -- Starlette's router rejects it (404, no matching
    route) before the request handler -- and therefore before any
    filesystem path is built from it -- ever runs. Stronger than 422: the
    handler's own validation is never even reached."""
    _patch_crew_builder(monkeypatch, pydantic_result=build_fixture_incident_report())

    response = client.post(f"/incidents/{bad_incident_id}/investigate")

    assert response.status_code == 404


# --- error handling: unknown incident -----------------------------------


def test_unknown_incident_returns_404(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_crew_builder(monkeypatch, pydantic_result=build_fixture_incident_report())

    response = client.post("/incidents/INC-DOES-NOT-EXIST/investigate")

    assert response.status_code == 404
    body = response.json()["detail"]
    assert body["status"] == "invalid"
    assert body["incident_report"] is None


# --- error handling: investigation-level failure -------------------------


def test_crew_exception_is_handled_gracefully(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_crew_builder(monkeypatch, raise_exc=RuntimeError("simulated LLM outage"))

    response = client.post("/incidents/INC-2026-0912/investigate")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "simulated LLM outage" in body["error"]
    assert body["incident_report"] is None
    assert body["requires_human_approval"] is True


def test_crew_returning_incomplete_report_is_handled(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    incomplete = build_fixture_incident_report().model_copy(update={"root_cause": ""})
    _patch_crew_builder(monkeypatch, pydantic_result=incomplete)

    response = client.post("/incidents/INC-2026-0912/investigate")

    assert response.status_code == 200
    assert response.json()["status"] == "failed"


# --- do not expose secrets ------------------------------------------------


def test_secret_is_never_exposed_in_the_response(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_secret = "super-secret-google-api-key-value"
    monkeypatch.setenv("GOOGLE_API_KEY", fake_secret)
    _patch_crew_builder(
        monkeypatch,
        raise_exc=RuntimeError(f"auth failed for key={fake_secret} against upstream API"),
    )

    response = client.post("/incidents/INC-2026-0912/investigate")

    assert response.status_code == 200
    assert fake_secret not in response.text
    assert "****" in response.json()["error"]


# --- do not execute production remediation --------------------------------


def test_every_recommendation_in_the_response_requires_human_approval(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_crew_builder(monkeypatch, pydantic_result=build_fixture_incident_report())

    response = client.post("/incidents/INC-2026-0912/investigate")

    report = response.json()["incident_report"]
    assert len(report["remediation_recommendations"]) > 0
    for rec in report["remediation_recommendations"]:
        assert rec["requires_human_approval"] is True


def test_response_model_has_no_endpoint_for_executing_remediation() -> None:
    from app.main import app as fastapi_app

    paths = {route.path for route in fastapi_app.routes if hasattr(route, "path")}
    assert not any("execute" in path or "apply" in path or "remediate" in path for path in paths)


# --- investigation status is always present -------------------------------


def test_response_always_includes_a_status_field(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_crew_builder(monkeypatch, pydantic_result=build_fixture_incident_report())

    response = client.post("/incidents/INC-2026-0912/investigate")

    assert response.json()["status"] in ("succeeded", "failed", "invalid")


# --- job-based endpoints: a job_id must match the incident_id it was ------
# --- actually started for -------------------------------------------------


def test_get_investigation_job_for_a_different_incident_id_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A job_id that genuinely exists -- just started for INC-2026-0912 --
    but requested under a different incident_id in the URL must 404, not
    silently return another incident's job data (app/api/incidents.py's
    `job.incident_id != incident_id` check)."""
    _patch_crew_builder(monkeypatch, pydantic_result=build_fixture_incident_report())

    start_response = client.post("/incidents/INC-2026-0912/investigations")
    assert start_response.status_code == 202
    job_id = start_response.json()["job_id"]

    # Let the (fake, offline) job finish before the test ends -- otherwise
    # its background thread can still be running when pytest tears down,
    # which is harmless but noisy.
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        status = client.get(f"/incidents/INC-2026-0912/investigations/{job_id}").json()["status"]
        if status != "running":
            break
        time.sleep(0.02)

    response = client.get(f"/incidents/INC-OTHER-INCIDENT/investigations/{job_id}")

    assert response.status_code == 404
