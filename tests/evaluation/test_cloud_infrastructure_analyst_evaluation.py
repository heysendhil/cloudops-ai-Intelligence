"""Golden-scenario evaluation for the Cloud Infrastructure Analyst Agent
against the real INC-2026-0912 incident metrics (see docs/evaluation.md).

This exercises a real LLM call via the Cloud Infrastructure Analyst Agent +
Cloud Infrastructure Analysis Task (no Crew involved -- Task.execute_sync
runs a single task against a single agent). It requires a real
GOOGLE_API_KEY and is skipped gracefully without one, per the project's
"handle missing API keys gracefully" rule.
"""

from __future__ import annotations

import pytest

from app.agents.cloud_infrastructure_analyst import build_cloud_infrastructure_analyst_agent
from app.llm_config import is_configured
from app.tasks.cloud_infrastructure_analysis_task import (
    CloudInfrastructureAnalysisReport,
    build_cloud_infrastructure_analysis_task,
)
from app.tools.cloud_metrics_tool import CloudMetricsTool

# Metrics that are known to be genuinely absent from data/metrics/payment-api.json
# (see Phase 7). A correct agent must never report a fabricated value for these.
UNAVAILABLE_METRICS = {"database_memory", "query_latency"}

pytestmark = [
    pytest.mark.live_llm,
    pytest.mark.skipif(
        not is_configured(),
        reason=(
            "GOOGLE_API_KEY is not set -- skipping live Cloud Infrastructure Analyst "
            "evaluation. Set it in backend/.env to run this evaluation against a real model."
        ),
    ),
]


@pytest.fixture(scope="module")
def evaluation_result() -> CloudInfrastructureAnalysisReport:
    agent = build_cloud_infrastructure_analyst_agent()
    task = build_cloud_infrastructure_analysis_task(agent)
    output = task.execute_sync(agent=agent)

    assert output.pydantic is not None, "Task did not produce structured output"
    return output.pydantic


@pytest.fixture(scope="module")
def ground_truth() -> dict:
    # The tool's own direct output is the ground truth the agent must not deviate from.
    tool = CloudMetricsTool()
    return tool.run()


def test_agent_identifies_at_least_one_observed_fact(
    evaluation_result: CloudInfrastructureAnalysisReport,
) -> None:
    assert len(evaluation_result.observed_facts) > 0


def test_agent_provides_interpretation_distinct_from_facts(
    evaluation_result: CloudInfrastructureAnalysisReport,
) -> None:
    assert evaluation_result.interpretation.strip() != ""


def test_agent_provides_at_least_one_possible_cause(
    evaluation_result: CloudInfrastructureAnalysisReport,
) -> None:
    assert len(evaluation_result.possible_causes) > 0


def test_agent_reports_confidence_in_valid_range(
    evaluation_result: CloudInfrastructureAnalysisReport,
) -> None:
    assert 0.0 <= evaluation_result.confidence <= 1.0


def test_agent_summary_is_non_empty(
    evaluation_result: CloudInfrastructureAnalysisReport,
) -> None:
    assert evaluation_result.summary.strip() != ""


def test_agent_never_reports_a_known_unavailable_metric(
    evaluation_result: CloudInfrastructureAnalysisReport,
) -> None:
    reported_metrics = {fact.metric for fact in evaluation_result.observed_facts}
    assert reported_metrics.isdisjoint(UNAVAILABLE_METRICS)


def test_agent_observed_facts_match_tool_ground_truth_exactly(
    evaluation_result: CloudInfrastructureAnalysisReport, ground_truth: dict
) -> None:
    for observed_fact in evaluation_result.observed_facts:
        assert observed_fact.metric in ground_truth, f"Unknown metric: {observed_fact.metric}"
        source = ground_truth[observed_fact.metric]

        if "points" in source:  # a MetricSeries
            assert source["available"] is True, (
                f"Agent reported a value for '{observed_fact.metric}', which the tool "
                "marked unavailable"
            )
            known_values = {(p["timestamp"], p["value"]) for p in source["points"]}
            assert (observed_fact.timestamp, observed_fact.value) in known_values, (
                f"Observed fact for '{observed_fact.metric}' does not match any value "
                "the tool actually returned"
            )
        else:  # a ScalarMetric (connection_limit)
            assert source["available"] is True
            assert observed_fact.value == source["value"]


def test_agent_identifies_database_pressure_as_abnormal(
    evaluation_result: CloudInfrastructureAnalysisReport,
) -> None:
    # The golden scenario's evidence centers on DB connection/resource pressure
    # (see docs/requirements.md); a competent analysis should surface it.
    reported_metrics = {fact.metric for fact in evaluation_result.observed_facts}
    assert reported_metrics & {"database_cpu", "database_connections", "active_connections"}
