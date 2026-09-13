"""Golden-scenario evaluation for the Kubernetes Reliability Analyst Agent
against the real INC-2026-0912 incident Kubernetes state (see
docs/evaluation.md).

This exercises a real LLM call via the Kubernetes Reliability Analyst Agent
+ Kubernetes Reliability Analysis Task (no Crew involved --
Task.execute_sync runs a single task against a single agent). It requires a
real GOOGLE_API_KEY and is skipped gracefully without one, per the
project's "handle missing API keys gracefully" rule.
"""

from __future__ import annotations

import pytest

from app.agents.kubernetes_reliability_analyst import (
    build_kubernetes_reliability_analyst_agent,
)
from app.llm_config import is_configured
from app.tasks.kubernetes_reliability_analysis_task import (
    KubernetesReliabilityReport,
    build_kubernetes_reliability_analysis_task,
)
from app.tools.kubernetes_reliability_tool import KubernetesReliabilityTool

pytestmark = [
    pytest.mark.live_llm,
    pytest.mark.skipif(
        not is_configured(),
        reason=(
            "GOOGLE_API_KEY is not set -- skipping live Kubernetes Reliability Analyst "
            "evaluation. Set it in backend/.env to run this evaluation against a real model."
        ),
    ),
]


@pytest.fixture(scope="module")
def evaluation_result() -> KubernetesReliabilityReport:
    agent = build_kubernetes_reliability_analyst_agent()
    task = build_kubernetes_reliability_analysis_task(agent)
    output = task.execute_sync(agent=agent)

    assert output.pydantic is not None, "Task did not produce structured output"
    return output.pydantic


@pytest.fixture(scope="module")
def ground_truth() -> dict:
    # The tool's own direct output is the ground truth the agent must not deviate from.
    tool = KubernetesReliabilityTool()
    return tool.run()


def test_agent_makes_a_deployment_health_determination(
    evaluation_result: KubernetesReliabilityReport,
) -> None:
    assert isinstance(evaluation_result.deployment_healthy, bool)
    assert evaluation_result.deployment_health_explanation.strip() != ""


def test_agent_identifies_pod_restart_patterns(
    evaluation_result: KubernetesReliabilityReport,
) -> None:
    # 4 of 6 pods restarted in the golden scenario; a competent analysis should surface them.
    assert len(evaluation_result.pod_restart_patterns) > 0


def test_agent_identifies_probe_failures(
    evaluation_result: KubernetesReliabilityReport,
) -> None:
    assert len(evaluation_result.probe_failures) > 0


def test_agent_cites_relevant_events(
    evaluation_result: KubernetesReliabilityReport,
) -> None:
    assert len(evaluation_result.relevant_events) > 0


def test_agent_makes_an_explicit_root_cause_assessment(
    evaluation_result: KubernetesReliabilityReport,
) -> None:
    assert evaluation_result.root_cause_assessment in (
        "likely_root_cause",
        "likely_consequence",
        "inconclusive",
    )
    assert evaluation_result.root_cause_reasoning.strip() != ""


def test_agent_does_not_default_to_root_cause_without_justification(
    evaluation_result: KubernetesReliabilityReport,
) -> None:
    # The golden scenario's actual root cause is database connection-pool exhaustion
    # (see docs/requirements.md); the pod restarts here are a downstream symptom.
    # A well-grounded agent reading only Kubernetes evidence may reasonably land on
    # "inconclusive" (it can't see the database side) but should not confidently
    # declare Kubernetes itself the root cause.
    assert evaluation_result.root_cause_assessment != "likely_root_cause"


def test_agent_reports_confidence_in_valid_range(
    evaluation_result: KubernetesReliabilityReport,
) -> None:
    assert 0.0 <= evaluation_result.confidence <= 1.0


def test_agent_summary_is_non_empty(evaluation_result: KubernetesReliabilityReport) -> None:
    assert evaluation_result.summary.strip() != ""


def test_agent_pod_restart_counts_match_tool_ground_truth(
    evaluation_result: KubernetesReliabilityReport, ground_truth: dict
) -> None:
    known_counts = {p["name"]: p["restart_count"] for p in ground_truth["pod_restart_counts"]}

    for finding in evaluation_result.pod_restart_patterns:
        assert finding.pod in known_counts, f"Unknown pod cited: {finding.pod}"
        assert finding.restart_count == known_counts[finding.pod], (
            f"Restart count for {finding.pod} does not match the tool's ground truth"
        )


def test_agent_cited_events_match_tool_ground_truth_verbatim(
    evaluation_result: KubernetesReliabilityReport, ground_truth: dict
) -> None:
    known_events = {
        (e["time"], e["reason"], e["involved_object"]) for e in ground_truth["events"]
    }

    for event in evaluation_result.relevant_events:
        assert (event.time, event.reason, event.involved_object) in known_events, (
            f"Cited event not found verbatim in tool output: {event!r}"
        )
