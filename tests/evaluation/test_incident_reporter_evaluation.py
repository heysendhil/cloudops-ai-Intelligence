"""Evaluation suite for the Incident Reporter Agent (see docs/evaluation.md).

Runs the agent for real against realistic fixture upstream reports
(grounded in the real INC-2026-0912 golden-scenario data -- see
tests/_fixtures_root_cause.py) via Task.execute_sync(agent=agent) (no Crew
involved, since it is not built yet). Covers the two requested test
categories: output structure and evidence grounding.

Requires a real GOOGLE_API_KEY and is skipped gracefully without one, per
the project's "handle missing API keys gracefully" rule.
"""

from __future__ import annotations

import re

import pytest

from app.agents.incident_reporter import build_incident_reporter_agent
from app.llm_config import is_configured
from app.tasks.incident_reporting_task import (
    DEFAULT_IMPACT,
    DEFAULT_INCIDENT_ID,
    DEFAULT_SERVICE,
    DEFAULT_SEVERITY,
    IncidentReport,
    build_incident_reporting_task,
)
from _fixtures_root_cause import (
    build_fixture_cloud_report,
    build_fixture_k8s_report,
    build_fixture_knowledge_report,
    build_fixture_log_report,
    build_fixture_rca_report,
    build_fixture_remediation_report,
)

pytestmark = [
    pytest.mark.live_llm,
    pytest.mark.skipif(
        not is_configured(),
        reason=(
            "GOOGLE_API_KEY is not set -- skipping live Incident Reporter evaluation. "
            "Set it in backend/.env to run this evaluation against a real model."
        ),
    ),
]


@pytest.fixture(scope="module")
def upstream():
    return {
        "log_analysis": build_fixture_log_report(),
        "cloud_analysis": build_fixture_cloud_report(),
        "kubernetes_analysis": build_fixture_k8s_report(),
        "knowledge_retrieval": build_fixture_knowledge_report(),
        "rca": build_fixture_rca_report(),
        "remediation": build_fixture_remediation_report(),
    }


@pytest.fixture(scope="module")
def evaluation_result(upstream: dict) -> IncidentReport:
    agent = build_incident_reporter_agent()
    task = build_incident_reporting_task(agent, **upstream)
    output = task.execute_sync(agent=agent)

    assert output.pydantic is not None, "Task did not produce structured output"
    return output.pydantic


# --- output structure -------------------------------------------------


def test_all_fourteen_sections_are_present_and_populated(
    evaluation_result: IncidentReport,
) -> None:
    assert evaluation_result.incident_id.strip() != ""
    assert evaluation_result.severity.strip() != ""
    assert evaluation_result.service.strip() != ""
    assert evaluation_result.impact.strip() != ""
    assert len(evaluation_result.timeline) > 0
    assert evaluation_result.log_findings.strip() != ""
    assert evaluation_result.cloud_findings.strip() != ""
    assert evaluation_result.kubernetes_findings.strip() != ""
    assert evaluation_result.relevant_runbook.strip() != ""
    assert evaluation_result.root_cause.strip() != ""
    assert len(evaluation_result.alternative_hypotheses) > 0
    assert 0.0 <= evaluation_result.confidence <= 1.0
    assert len(evaluation_result.remediation_recommendations) > 0
    assert evaluation_result.human_approval_requirement.strip() != ""


def test_incident_metadata_is_copied_exactly(evaluation_result: IncidentReport) -> None:
    assert evaluation_result.incident_id == DEFAULT_INCIDENT_ID
    assert evaluation_result.severity == DEFAULT_SEVERITY
    assert evaluation_result.service == DEFAULT_SERVICE
    assert evaluation_result.impact == DEFAULT_IMPACT


def test_every_remediation_recommendation_still_requires_human_approval(
    evaluation_result: IncidentReport,
) -> None:
    for rec in evaluation_result.remediation_recommendations:
        assert rec.requires_human_approval is True


def test_human_approval_requirement_states_the_safety_property(
    evaluation_result: IncidentReport,
) -> None:
    text = evaluation_result.human_approval_requirement.lower()
    assert "approval" in text
    assert "human" in text


# --- evidence grounding -----------------------------------------------


def test_timeline_timestamps_are_grounded_in_the_upstream_reports(
    evaluation_result: IncidentReport, upstream: dict
) -> None:
    known_timestamps = set(upstream["log_analysis"].timestamps)
    known_timestamps.update(f.timestamp for f in upstream["cloud_analysis"].observed_facts)
    known_timestamps.update(e.time for e in upstream["kubernetes_analysis"].relevant_events)

    for entry in evaluation_result.timeline:
        assert entry.timestamp in known_timestamps, (
            f"Timeline entry timestamp not found in any of the three source reports: "
            f"{entry.timestamp!r}"
        )


def test_remediation_recommendations_match_the_advisor_report_exactly(
    evaluation_result: IncidentReport, upstream: dict
) -> None:
    known_actions = {rec.action for rec in upstream["remediation"].recommendations}
    reported_actions = {rec.action for rec in evaluation_result.remediation_recommendations}

    assert reported_actions == known_actions, (
        "Reported recommendations do not exactly match the Remediation Advisor's report "
        "-- the Incident Reporter must carry them through unaltered."
    )


def _known_terms(*reports) -> set[str]:
    combined = " ".join(r.model_dump_json() for r in reports).lower()
    return set(re.findall(r"[a-z]{5,}", combined))


def test_log_findings_overlap_with_the_log_analyst_report(
    evaluation_result: IncidentReport, upstream: dict
) -> None:
    known_terms = _known_terms(upstream["log_analysis"])
    reported_terms = set(re.findall(r"[a-z]{5,}", evaluation_result.log_findings.lower()))

    assert reported_terms & known_terms


def test_cloud_findings_overlap_with_the_cloud_analyst_report(
    evaluation_result: IncidentReport, upstream: dict
) -> None:
    known_terms = _known_terms(upstream["cloud_analysis"])
    reported_terms = set(re.findall(r"[a-z]{5,}", evaluation_result.cloud_findings.lower()))

    assert reported_terms & known_terms


def test_kubernetes_findings_overlap_with_the_kubernetes_analyst_report(
    evaluation_result: IncidentReport, upstream: dict
) -> None:
    known_terms = _known_terms(upstream["kubernetes_analysis"])
    reported_terms = set(re.findall(r"[a-z]{5,}", evaluation_result.kubernetes_findings.lower()))

    assert reported_terms & known_terms


def test_relevant_runbook_overlaps_with_the_knowledge_report(
    evaluation_result: IncidentReport, upstream: dict
) -> None:
    known_terms = _known_terms(upstream["knowledge_retrieval"])
    reported_terms = set(re.findall(r"[a-z]{5,}", evaluation_result.relevant_runbook.lower()))

    assert reported_terms & known_terms


def test_root_cause_and_confidence_are_consistent_with_the_rca_report(
    evaluation_result: IncidentReport, upstream: dict
) -> None:
    known_terms = _known_terms(upstream["rca"])
    reported_terms = set(re.findall(r"[a-z]{5,}", evaluation_result.root_cause.lower()))

    assert reported_terms & known_terms
    # confidence should not drift wildly from the RCA's own calibrated confidence
    assert abs(evaluation_result.confidence - upstream["rca"].confidence) <= 0.25
