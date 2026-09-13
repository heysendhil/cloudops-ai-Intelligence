"""Formal evaluation suite for the Root Cause Investigator Agent against the
real INC-2026-0912 golden scenario (see docs/evaluation.md).

Runs the full four-analyst pipeline for real (Log Analyst, Cloud
Infrastructure Analyst, Kubernetes Reliability Analyst, Knowledge/RAG
Agent), then the Root Cause Investigator over their real outputs -- five
live LLM calls total, each via Task.execute_sync(agent=agent) (no Crew
involved, since it is not built yet). Scores the result with the
deterministic rubric in app.evaluation.root_cause_rubric and asserts the
target score (>= 85%, see docs/evaluation.md and TARGET_SCORE).

Requires a real GOOGLE_API_KEY and is skipped gracefully without one, per
the project's "handle missing API keys gracefully" rule.
"""

from __future__ import annotations

import pytest

from app.agents.cloud_infrastructure_analyst import build_cloud_infrastructure_analyst_agent
from app.agents.knowledge_rag import build_knowledge_rag_agent
from app.agents.kubernetes_reliability_analyst import (
    build_kubernetes_reliability_analyst_agent,
)
from app.agents.log_analyst import build_log_analyst_agent
from app.agents.root_cause_investigator import build_root_cause_investigator_agent
from app.evaluation.root_cause_rubric import TARGET_SCORE, score_root_cause_report
from app.llm_config import is_configured
from app.tasks.cloud_infrastructure_analysis_task import build_cloud_infrastructure_analysis_task
from app.tasks.knowledge_retrieval_task import build_knowledge_retrieval_task
from app.tasks.kubernetes_reliability_analysis_task import (
    build_kubernetes_reliability_analysis_task,
)
from app.tasks.log_analysis_task import build_log_analysis_task
from app.tasks.root_cause_investigation_task import (
    RootCauseInvestigationReport,
    build_root_cause_investigation_task,
)

pytestmark = [
    pytest.mark.live_llm,
    pytest.mark.skipif(
        not is_configured(),
        reason=(
            "GOOGLE_API_KEY is not set -- skipping live Root Cause Investigator evaluation. "
            "Set it in backend/.env to run this evaluation against a real model."
        ),
    ),
]


@pytest.fixture(scope="module")
def upstream_reports() -> dict:
    log_agent = build_log_analyst_agent()
    log_task = build_log_analysis_task(log_agent)
    log_output = log_task.execute_sync(agent=log_agent)

    cloud_agent = build_cloud_infrastructure_analyst_agent()
    cloud_task = build_cloud_infrastructure_analysis_task(cloud_agent)
    cloud_output = cloud_task.execute_sync(agent=cloud_agent)

    k8s_agent = build_kubernetes_reliability_analyst_agent()
    k8s_task = build_kubernetes_reliability_analysis_task(k8s_agent)
    k8s_output = k8s_task.execute_sync(agent=k8s_agent)

    knowledge_agent = build_knowledge_rag_agent()
    knowledge_task = build_knowledge_retrieval_task(knowledge_agent)
    knowledge_output = knowledge_task.execute_sync(agent=knowledge_agent)

    return {
        "log_analysis": log_output.pydantic,
        "cloud_analysis": cloud_output.pydantic,
        "kubernetes_analysis": k8s_output.pydantic,
        "knowledge_retrieval": knowledge_output.pydantic,
    }


@pytest.fixture(scope="module")
def evaluation_result(upstream_reports: dict) -> RootCauseInvestigationReport:
    agent = build_root_cause_investigator_agent()
    task = build_root_cause_investigation_task(agent, **upstream_reports)
    output = task.execute_sync(agent=agent)

    assert output.pydantic is not None, "Task did not produce structured output"
    return output.pydantic


def test_report_produces_a_root_cause(evaluation_result: RootCauseInvestigationReport) -> None:
    assert evaluation_result.root_cause.strip() != ""


def test_formal_rubric_score_meets_target(
    evaluation_result: RootCauseInvestigationReport, upstream_reports: dict
) -> None:
    result = score_root_cause_report(evaluation_result, **upstream_reports)

    failing = [(c.name, c.detail) for c in result.criteria if not c.passed]
    assert result.overall_score >= TARGET_SCORE, (
        f"Root Cause Investigator scored {result.overall_score:.0%}, below the "
        f"{TARGET_SCORE:.0%} target. Failing criteria: {failing}"
    )


def test_report_identifies_database_connection_pressure_as_root_cause(
    evaluation_result: RootCauseInvestigationReport,
) -> None:
    # The golden scenario's actual root cause is database connection pool exhaustion
    # (see docs/requirements.md); a well-grounded investigation should land on it.
    text = evaluation_result.root_cause.lower()
    assert "connection" in text or "pool" in text or "database" in text
