"""End-to-end evaluation of the CloudOps Investigation Crew: a complete,
real simulated investigation of INC-2026-0912 (see docs/evaluation.md),
via crew.kickoff() -- Process.sequential, all 7 agents/tasks, context
passed downstream by CrewAI itself (not pre-computed).

Requires a real GOOGLE_API_KEY and is skipped gracefully without one, per
the project's "handle missing API keys gracefully" rule.
"""

from __future__ import annotations

import pytest

from app.crew import build_cloudops_investigation_crew
from app.llm_config import is_configured
from app.tasks.cloud_infrastructure_analysis_task import CloudInfrastructureAnalysisReport
from app.tasks.incident_reporting_task import IncidentReport
from app.tasks.knowledge_retrieval_task import KnowledgeRetrievalReport
from app.tasks.kubernetes_reliability_analysis_task import KubernetesReliabilityReport
from app.tasks.log_analysis_task import LogAnalysisReport
from app.tasks.remediation_recommendation_task import RemediationRecommendationReport
from app.tasks.root_cause_investigation_task import RootCauseInvestigationReport

EXPECTED_TASK_OUTPUT_TYPES = [
    LogAnalysisReport,
    CloudInfrastructureAnalysisReport,
    KubernetesReliabilityReport,
    KnowledgeRetrievalReport,
    RootCauseInvestigationReport,
    RemediationRecommendationReport,
    IncidentReport,
]

pytestmark = [
    pytest.mark.live_llm,
    pytest.mark.skipif(
        not is_configured(),
        reason=(
            "GOOGLE_API_KEY is not set -- skipping the live CloudOps Investigation Crew run. "
            "Set it in backend/.env to run a complete simulated investigation against a real model."
        ),
    ),
]


@pytest.fixture(scope="module")
def crew_result():
    crew = build_cloudops_investigation_crew()
    return crew.kickoff()


def test_all_seven_tasks_completed(crew_result) -> None:
    assert len(crew_result.tasks_output) == 7


def test_each_task_produced_the_expected_structured_output_type(crew_result) -> None:
    for task_output, expected_type in zip(crew_result.tasks_output, EXPECTED_TASK_OUTPUT_TYPES):
        assert task_output.pydantic is not None, f"{task_output.name} produced no structured output"
        assert isinstance(task_output.pydantic, expected_type)


def test_no_tool_failures_across_the_whole_investigation(crew_result) -> None:
    assert crew_result.tool_failures == []


def test_final_output_is_the_incident_report(crew_result) -> None:
    assert isinstance(crew_result.pydantic, IncidentReport)


def test_final_incident_report_identifies_the_golden_scenario_incident(crew_result) -> None:
    report = crew_result.pydantic

    assert report.incident_id == "INC-2026-0912"
    assert report.severity == "SEV-2"
    assert report.service == "Payment API"


def test_final_incident_report_has_remediation_requiring_human_approval(crew_result) -> None:
    report = crew_result.pydantic

    assert len(report.remediation_recommendations) > 0
    assert all(rec.requires_human_approval is True for rec in report.remediation_recommendations)
