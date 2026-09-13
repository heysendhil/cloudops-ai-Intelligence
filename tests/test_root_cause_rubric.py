"""Unit tests for the Root Cause Investigator's formal evaluation rubric
(app.evaluation.root_cause_rubric). These run entirely offline against
synthetic fixture reports -- no LLM, no API key -- to verify the scorer
itself is correct before it's ever pointed at a live model output.
"""

from app.evaluation.root_cause_rubric import TARGET_SCORE, score_root_cause_report
from app.tasks.root_cause_investigation_task import (
    AlternativeHypothesis,
    EvidenceItem,
    RootCauseInvestigationReport,
)
from _fixtures_root_cause import (
    build_fixture_cloud_report,
    build_fixture_k8s_report,
    build_fixture_knowledge_report,
    build_fixture_log_report,
)


def _upstream_reports():
    return (
        build_fixture_log_report(),
        build_fixture_cloud_report(),
        build_fixture_k8s_report(),
        build_fixture_knowledge_report(),
    )


def _good_report() -> RootCauseInvestigationReport:
    return RootCauseInvestigationReport(
        root_cause=(
            "Database connection pool exhaustion: a concurrent batch job increased query "
            "duration, saturating the fixed-size HikariCP pool (utilization reached 100%) "
            "and driving database CPU to 92%, which caused request queuing (latency up to "
            "4300ms), timeouts, and downstream pod restarts via liveness probe failures."
        ),
        evidence=[
            EvidenceItem(
                source_agent="Cloud Infrastructure Analyst",
                fact="Database connection pool utilization reached 100%",
                reference="database_connections=100.0% at 2026-09-12T14:08:00Z",
            ),
            EvidenceItem(
                source_agent="Cloud Infrastructure Analyst",
                fact="Database CPU peaked at 92%, exceeding application pod CPU",
                reference="database_cpu=92% at 2026-09-12T14:13:50Z",
            ),
            EvidenceItem(
                source_agent="Log Analyst",
                fact="HikariCP connections timed out after 30000ms",
                reference=(
                    "HikariPool-1 - Connection is not available, request timed out after 30000ms."
                ),
            ),
        ],
        alternative_hypotheses=[
            AlternativeHypothesis(
                hypothesis=(
                    "A Kubernetes-level issue (e.g. a bad deployment or node problem) "
                    "independently caused the outage"
                ),
                supporting_evidence=["4 of 6 pods restarted with liveness probe failures"],
                why_less_likely_than_leading=(
                    "The Kubernetes Reliability Analyst assessed the restarts as "
                    "likely_consequence rather than likely_root_cause, since probe failures "
                    "coincide with the same window the DB pool was saturated at 100%, and no "
                    "deployment change occurred during the incident."
                ),
            )
        ],
        confidence=0.75,
        missing_evidence=[
            "Direct database-side query execution logs or performance-insights data to "
            "confirm exactly which queries held connections longest during the incident.",
        ],
    )


def _bad_report() -> RootCauseInvestigationReport:
    return RootCauseInvestigationReport(
        root_cause=(
            "High latency and HTTP 500 errors occurred, with CPU utilization reaching 99% "
            "and pod restarts observed."
        ),
        evidence=[],
        alternative_hypotheses=[],
        confidence=1.0,
        missing_evidence=[],
    )


# --- overall scoring behavior ----------------------------------------------


def test_good_report_scores_at_or_above_target() -> None:
    report = _good_report()

    result = score_root_cause_report(report, *_upstream_reports())

    assert result.overall_score >= TARGET_SCORE
    assert result.passed_target is True
    assert all(c.passed for c in result.criteria), [
        (c.name, c.detail) for c in result.criteria if not c.passed
    ]


def test_bad_report_scores_well_below_target() -> None:
    report = _bad_report()

    result = score_root_cause_report(report, *_upstream_reports())

    assert result.overall_score < 0.5
    assert result.passed_target is False


def test_rubric_has_seven_equally_weighted_criteria() -> None:
    result = score_root_cause_report(_good_report(), *_upstream_reports())

    assert len(result.criteria) == 7
    weights = {c.weight for c in result.criteria}
    assert weights == {1.0}


def test_result_to_dict_is_json_serializable() -> None:
    import json

    result = score_root_cause_report(_good_report(), *_upstream_reports())

    serialized = json.dumps(result.to_dict())
    assert "overall_score" in serialized
    assert "criteria" in serialized


# --- individual criteria -------------------------------------------------


def test_criterion_no_invented_metrics_flags_an_unknown_number() -> None:
    report = _good_report()
    bad_report = report.model_copy(
        update={
            "root_cause": report.root_cause + " Also, error rate hit 63% at one point.",
        }
    )

    result = score_root_cause_report(bad_report, *_upstream_reports())

    criterion = next(c for c in result.criteria if c.name == "no_invented_metrics")
    assert criterion.passed is False
    assert "63" in criterion.detail


def test_criterion_confidence_calibrated_rejects_boundary_values() -> None:
    for boundary in (0.0, 1.0):
        report = _good_report().model_copy(update={"confidence": boundary})

        result = score_root_cause_report(report, *_upstream_reports())

        criterion = next(c for c in result.criteria if c.name == "confidence_calibrated")
        assert criterion.passed is False


def test_criterion_alternative_hypotheses_rejects_empty_list() -> None:
    report = _good_report().model_copy(update={"alternative_hypotheses": []})

    result = score_root_cause_report(report, *_upstream_reports())

    criterion = next(c for c in result.criteria if c.name == "alternative_hypotheses_identified")
    assert criterion.passed is False


def test_criterion_alternative_hypotheses_rejects_hypothesis_identical_to_root_cause() -> None:
    report = _good_report()
    duplicate = report.model_copy(
        update={
            "alternative_hypotheses": [
                AlternativeHypothesis(
                    hypothesis=report.root_cause,  # not actually a different hypothesis
                    supporting_evidence=[],
                    why_less_likely_than_leading="N/A, this is the same as the leading hypothesis.",
                )
            ]
        }
    )

    result = score_root_cause_report(duplicate, *_upstream_reports())

    criterion = next(c for c in result.criteria if c.name == "alternative_hypotheses_identified")
    assert criterion.passed is False


def test_criterion_leading_hypothesis_justified_rejects_thin_justification() -> None:
    report = _good_report()
    thin = report.model_copy(
        update={
            "alternative_hypotheses": [
                AlternativeHypothesis(
                    hypothesis="Something else entirely",
                    supporting_evidence=[],
                    why_less_likely_than_leading="No.",  # too thin
                )
            ]
        }
    )

    result = score_root_cause_report(thin, *_upstream_reports())

    criterion = next(c for c in result.criteria if c.name == "leading_hypothesis_justified")
    assert criterion.passed is False


def test_criterion_missing_evidence_rejects_empty_list() -> None:
    report = _good_report().model_copy(update={"missing_evidence": []})

    result = score_root_cause_report(report, *_upstream_reports())

    criterion = next(c for c in result.criteria if c.name == "missing_evidence_identified")
    assert criterion.passed is False


def test_criterion_root_cause_not_just_symptoms_rejects_pure_symptom_restatement() -> None:
    report = _good_report().model_copy(
        update={"root_cause": "High latency, HTTP 500 errors, and pod restarts occurred."}
    )

    result = score_root_cause_report(report, *_upstream_reports())

    criterion = next(c for c in result.criteria if c.name == "root_cause_not_just_symptoms")
    assert criterion.passed is False


def test_criterion_evidence_based_reasoning_rejects_unrecognized_source_agent() -> None:
    report = _good_report()
    bad_source = report.model_copy(
        update={
            "evidence": report.evidence
            + [
                EvidenceItem(
                    source_agent="Some Other Agent",
                    fact="made up",
                    reference="nowhere",
                )
            ]
        }
    )

    result = score_root_cause_report(bad_source, *_upstream_reports())

    criterion = next(c for c in result.criteria if c.name == "evidence_based_reasoning")
    assert criterion.passed is False


def test_single_failing_criterion_still_scores_near_but_below_full() -> None:
    # Six of seven criteria pass; only root_cause_not_just_symptoms fails.
    report = _good_report().model_copy(
        update={"root_cause": "High latency, HTTP 500 errors, and pod restarts occurred."}
    )

    result = score_root_cause_report(report, *_upstream_reports())

    assert result.overall_score == 6 / 7
