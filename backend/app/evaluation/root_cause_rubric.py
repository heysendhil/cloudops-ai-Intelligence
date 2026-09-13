"""Formal evaluation rubric for the Root Cause Investigator Agent.

Scores a RootCauseInvestigationReport against seven deterministic criteria,
one per requirement in docs/agent-design.md's Root Cause Investigator spec.
Every criterion is a plain, reproducible Python check -- no second LLM call
("LLM-as-judge") is used, so scoring is deterministic and runs offline.
This module has no CrewAI or LLM dependency; it is pure evaluation logic
over already-produced report objects, reusable from both automated tests
and any future manual review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.tasks.cloud_infrastructure_analysis_task import CloudInfrastructureAnalysisReport
from app.tasks.knowledge_retrieval_task import KnowledgeRetrievalReport
from app.tasks.kubernetes_reliability_analysis_task import KubernetesReliabilityReport
from app.tasks.log_analysis_task import LogAnalysisReport
from app.tasks.root_cause_investigation_task import RootCauseInvestigationReport

TARGET_SCORE = 0.85

_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")

# Terms indicating the text names an underlying mechanism/cause rather than
# only restating an observable symptom. Not exhaustive -- a deliberately
# broad list covering the kinds of root causes this project's incidents
# involve (resource exhaustion, contention, config/capacity issues).
_MECHANISM_TERMS = (
    "pool",
    "exhaust",
    "connection",
    "capacity",
    "timeout",
    "query",
    "lock",
    "contention",
    "leak",
    "misconfigur",
    "resource",
    "saturat",
    "limit",
    "throttl",
    "deploy",
    "migration",
    "bug",
    "regression",
)

# Symptom-only terms: if root_cause contains ONLY these and no mechanism
# term, it's describing an effect, not a cause.
_SYMPTOM_ONLY_TERMS = ("latency", "error rate", "5xx", "500", "restart", "slow", "down")


@dataclass(frozen=True)
class CriterionResult:
    name: str
    weight: float
    passed: bool
    detail: str


@dataclass(frozen=True)
class RubricResult:
    criteria: list[CriterionResult] = field(default_factory=list)

    @property
    def overall_score(self) -> float:
        total_weight = sum(c.weight for c in self.criteria)
        if total_weight == 0:
            return 0.0
        earned = sum(c.weight for c in self.criteria if c.passed)
        return earned / total_weight

    @property
    def passed_target(self) -> bool:
        return self.overall_score >= TARGET_SCORE

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "passed_target": self.passed_target,
            "target_score": TARGET_SCORE,
            "criteria": [
                {
                    "name": c.name,
                    "weight": c.weight,
                    "passed": c.passed,
                    "detail": c.detail,
                }
                for c in self.criteria
            ],
        }


def _normalize_number(raw: str) -> str:
    # "100" and "100.0" (e.g. prose vs. a JSON-dumped float field) must
    # compare equal -- normalize via float round-tripping.
    value = float(raw)
    if value == int(value):
        return str(int(value))
    return str(value)


def _extract_numbers(text: str) -> set[str]:
    return {_normalize_number(match) for match in _NUMBER_PATTERN.findall(text)}


def _known_numbers(
    log_analysis: LogAnalysisReport,
    cloud_analysis: CloudInfrastructureAnalysisReport,
    kubernetes_analysis: KubernetesReliabilityReport,
    knowledge_retrieval: KnowledgeRetrievalReport,
) -> set[str]:
    combined = "\n".join(
        report.model_dump_json()
        for report in (log_analysis, cloud_analysis, kubernetes_analysis, knowledge_retrieval)
    )
    return _extract_numbers(combined)


VALID_SOURCE_AGENTS = {
    "log analyst",
    "cloud infrastructure analyst",
    "kubernetes reliability analyst",
    "knowledge/rag agent",
}


def _check_evidence_based_reasoning(report: RootCauseInvestigationReport) -> CriterionResult:
    valid_items = [
        item for item in report.evidence if item.source_agent.strip().lower() in VALID_SOURCE_AGENTS
    ]
    passed = len(report.evidence) >= 2 and len(valid_items) == len(report.evidence)
    detail = (
        f"{len(report.evidence)} evidence item(s), {len(valid_items)} with a recognized "
        "source_agent (need >=2 total, all recognized)."
    )
    return CriterionResult("evidence_based_reasoning", 1.0, passed, detail)


def _check_no_invented_metrics(
    report: RootCauseInvestigationReport,
    log_analysis: LogAnalysisReport,
    cloud_analysis: CloudInfrastructureAnalysisReport,
    kubernetes_analysis: KubernetesReliabilityReport,
    knowledge_retrieval: KnowledgeRetrievalReport,
) -> CriterionResult:
    known = _known_numbers(log_analysis, cloud_analysis, kubernetes_analysis, knowledge_retrieval)
    claimed_parts = [report.root_cause]
    claimed_parts.extend(f"{item.fact} {item.reference}" for item in report.evidence)
    claimed_parts.extend(
        f"{h.hypothesis} {' '.join(h.supporting_evidence)} {h.why_less_likely_than_leading}"
        for h in report.alternative_hypotheses
    )
    claimed_parts.extend(report.missing_evidence)
    claimed_numbers = _extract_numbers(" ".join(claimed_parts))
    unknown_numbers = claimed_numbers - known
    passed = len(unknown_numbers) == 0
    detail = (
        "All numeric claims traced to the four reports."
        if passed
        else f"Numbers not found in any of the four reports: {sorted(unknown_numbers)}"
    )
    return CriterionResult("no_invented_metrics", 1.0, passed, detail)


def _check_alternative_hypotheses(report: RootCauseInvestigationReport) -> CriterionResult:
    distinct = [
        h for h in report.alternative_hypotheses
        if h.hypothesis.strip().lower() != report.root_cause.strip().lower() and h.hypothesis.strip()
    ]
    passed = len(distinct) >= 1
    detail = f"{len(distinct)} distinct alternative hypothesis(es) (need >=1)."
    return CriterionResult("alternative_hypotheses_identified", 1.0, passed, detail)


def _check_leading_hypothesis_justified(report: RootCauseInvestigationReport) -> CriterionResult:
    if not report.alternative_hypotheses:
        return CriterionResult(
            "leading_hypothesis_justified", 1.0, False, "No alternative hypotheses to justify against."
        )
    justified = [
        h for h in report.alternative_hypotheses if len(h.why_less_likely_than_leading.strip()) >= 15
    ]
    passed = len(justified) == len(report.alternative_hypotheses)
    detail = f"{len(justified)}/{len(report.alternative_hypotheses)} alternatives have a substantive why_less_likely_than_leading."
    return CriterionResult("leading_hypothesis_justified", 1.0, passed, detail)


def _check_missing_evidence_identified(report: RootCauseInvestigationReport) -> CriterionResult:
    meaningful = [e for e in report.missing_evidence if len(e.strip()) >= 10]
    passed = len(meaningful) >= 1
    detail = f"{len(meaningful)} meaningful missing_evidence item(s) (need >=1)."
    return CriterionResult("missing_evidence_identified", 1.0, passed, detail)


def _check_confidence_calibrated(report: RootCauseInvestigationReport) -> CriterionResult:
    passed = 0.0 < report.confidence < 1.0
    detail = f"confidence={report.confidence} (must be strictly between 0.0 and 1.0)."
    return CriterionResult("confidence_calibrated", 1.0, passed, detail)


def _check_root_cause_not_just_symptoms(report: RootCauseInvestigationReport) -> CriterionResult:
    text = report.root_cause.lower()
    has_mechanism = any(term in text for term in _MECHANISM_TERMS)
    passed = bool(text.strip()) and has_mechanism
    detail = (
        "root_cause names an underlying mechanism, not only symptoms."
        if passed
        else "root_cause does not clearly name an underlying mechanism (may just restate symptoms)."
    )
    return CriterionResult("root_cause_not_just_symptoms", 1.0, passed, detail)


def score_root_cause_report(
    report: RootCauseInvestigationReport,
    log_analysis: LogAnalysisReport,
    cloud_analysis: CloudInfrastructureAnalysisReport,
    kubernetes_analysis: KubernetesReliabilityReport,
    knowledge_retrieval: KnowledgeRetrievalReport,
) -> RubricResult:
    """Score a RootCauseInvestigationReport against the seven required
    criteria (evidence-based reasoning, no invented metrics, alternative
    hypotheses, leading-hypothesis justification, missing evidence,
    calibrated confidence, root-cause-vs-symptom distinction). Each
    criterion is weighted equally; overall_score is the fraction of total
    weight passed.
    """
    criteria = [
        _check_evidence_based_reasoning(report),
        _check_no_invented_metrics(
            report, log_analysis, cloud_analysis, kubernetes_analysis, knowledge_retrieval
        ),
        _check_alternative_hypotheses(report),
        _check_leading_hypothesis_justified(report),
        _check_missing_evidence_identified(report),
        _check_confidence_calibrated(report),
        _check_root_cause_not_just_symptoms(report),
    ]
    return RubricResult(criteria=criteria)
