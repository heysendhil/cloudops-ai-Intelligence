"""Shared fixture builders for the four upstream analyst reports, used by
the Root Cause Investigator's wiring tests, rubric unit tests, and
evaluation suite. Not a test module itself (no test_ prefix).

Values are grounded in the real Phase 3 golden-scenario data (INC-2026-0912)
so rubric checks that cross-reference numbers behave realistically.
"""

from __future__ import annotations

from app.tasks.cloud_infrastructure_analysis_task import (
    CloudInfrastructureAnalysisReport,
    ObservedMetricFact,
)
from app.tasks.knowledge_retrieval_task import (
    CitedKnowledgeChunk,
    KnowledgeRetrievalReport,
    TroubleshootingProcedure,
)
from app.tasks.kubernetes_reliability_analysis_task import (
    CitedKubernetesEvent,
    KubernetesReliabilityReport,
    PodRestartPatternFinding,
    ProbeFailureFinding,
)
from app.tasks.incident_reporting_task import IncidentReport, TimelineEntry
from app.tasks.log_analysis_task import LogAnalysisFinding, LogAnalysisReport, RecurringLogPattern
from app.tasks.remediation_recommendation_task import Recommendation, RemediationRecommendationReport
from app.tasks.root_cause_investigation_task import (
    AlternativeHypothesis,
    EvidenceItem,
    RootCauseInvestigationReport,
)


def build_fixture_log_report() -> LogAnalysisReport:
    return LogAnalysisReport(
        errors=[
            LogAnalysisFinding(
                level="ERROR",
                line_number=17,
                timestamp="2026-09-12T14:06:18Z",
                raw_line=(
                    "payment-api-7f9c9d6b78-t2tuc 2026-09-12 14:06:18.209 ERROR 1 --- "
                    "[nio-8080-exec-3] c.p.web.GlobalExceptionHandler : Request POST "
                    "/api/v1/payments/charge failed, responded 500 (request_id=req_4f0a9c1e)"
                ),
                description="Charge request failed with HTTP 500 due to a JDBC connection timeout.",
            )
        ],
        warnings=[
            LogAnalysisFinding(
                level="WARN",
                line_number=15,
                timestamp="2026-09-12T14:05:10Z",
                raw_line=(
                    "payment-api-7f9c9d6b78-h5f7r 2026-09-12 14:05:10.442 WARN 1 --- "
                    "[nio-8080-exec-1] com.zaxxer.hikari.pool.HikariPool : HikariPool-1 - "
                    "Connection is not available, request timed out after 30000ms."
                ),
                description="HikariCP could not obtain a connection within the 30000ms timeout.",
            )
        ],
        recurring_patterns=[
            RecurringLogPattern(
                description="Repeated HikariPool connection-timeout warnings across pods.",
                occurrences=2,
                line_numbers=[15, 34],
            )
        ],
        timestamps=["2026-09-12T14:05:10Z", "2026-09-12T14:06:18Z"],
        evidence=[
            "HikariPool-1 - Connection is not available, request timed out after 30000ms.",
        ],
        summary="HikariCP connection pool exhaustion caused timeouts and HTTP 500 errors.",
        confidence=0.8,
    )


def build_fixture_cloud_report() -> CloudInfrastructureAnalysisReport:
    return CloudInfrastructureAnalysisReport(
        observed_facts=[
            ObservedMetricFact(
                metric="database_connections",
                value=100.0,
                unit="percent",
                timestamp="2026-09-12T14:08:00Z",
                source_field="db_pool_utilization_pct",
                relationship_to_incident="Pool utilization reached 100% right as 5xx errors and latency spiked.",
            ),
            ObservedMetricFact(
                metric="database_cpu",
                value=92,
                unit="percent",
                timestamp="2026-09-12T14:13:50Z",
                source_field="db_cpu_utilization_pct",
                relationship_to_incident="Database CPU peaked at 92%, well above the application pods' own CPU.",
            ),
            ObservedMetricFact(
                metric="request_latency",
                value=4300,
                unit="ms",
                timestamp="2026-09-12T14:13:50Z",
                source_field="latency_ms_avg",
                relationship_to_incident="Average request latency peaked at 4300ms during the same window.",
            ),
        ],
        interpretation=(
            "The database connection pool saturated at 100% utilization while database CPU "
            "climbed to 92%, well above application pod CPU, indicating the database itself "
            "was the bottleneck rather than the application layer."
        ),
        possible_causes=[
            "A concurrent batch job increased query duration, holding connections longer than usual.",
        ],
        summary="Database connection pool exhaustion correlated with elevated latency and 5xx errors.",
        confidence=0.75,
    )


def build_fixture_k8s_report() -> KubernetesReliabilityReport:
    return KubernetesReliabilityReport(
        deployment_healthy=True,
        deployment_health_explanation="All 6/6 replicas are ready and available as of the snapshot.",
        pod_restart_patterns=[
            PodRestartPatternFinding(
                pod="payment-api-7f9c9d6b78-x4k2p",
                restart_count=1,
                pattern_description=(
                    "Restarted once after 3 consecutive liveness probe failures roughly 10s apart."
                ),
            )
        ],
        probe_failures=[
            ProbeFailureFinding(
                pod="payment-api-7f9c9d6b78-x4k2p",
                probe_type="liveness",
                failure_count=3,
                description="Liveness probe failed 3 times before the pod was killed and restarted.",
            )
        ],
        relevant_events=[
            CitedKubernetesEvent(
                time="2026-09-12T14:10:15Z",
                type="Normal",
                reason="Killing",
                involved_object="pod/payment-api-7f9c9d6b78-x4k2p",
                message="Container payment-api failed liveness probe, will be restarted",
            )
        ],
        root_cause_assessment="likely_consequence",
        root_cause_reasoning=(
            "The liveness probe hits an endpoint that itself depends on a database connection; "
            "probe failures line up with the same window the connection pool was saturated, so "
            "the restarts look like a downstream consequence rather than an independent cause."
        ),
        summary="4 of 6 pods restarted due to liveness probe failures tied to DB connection pressure.",
        confidence=0.7,
    )


def build_fixture_knowledge_report() -> KnowledgeRetrievalReport:
    return KnowledgeRetrievalReport(
        query="database connection pool exhaustion causing elevated latency and pod restarts",
        retrieved_knowledge=[
            CitedKnowledgeChunk(
                text=(
                    "## Likely Causes\n\n- **Long-running or newly slow queries** holding "
                    "connections far longer than usual."
                ),
                source_path="data/runbooks/database-connection-pool.md",
                source_file="database-connection-pool.md",
                title="Runbook: Database Connection Pool Exhaustion",
                heading="Likely Causes",
                relevance_to_incident="Matches the observed pool saturation and elevated DB CPU.",
            )
        ],
        troubleshooting_procedures=[
            TroubleshootingProcedure(
                description="Check for a concurrent batch job overlapping the incident window.",
                source_heading="Diagnosis Steps",
                safety_note="Advisory only -- requires human review before action.",
            )
        ],
        knowledge_vs_evidence_note=(
            "The above is general runbook guidance, not a confirmed fact about this incident."
        ),
        production_safety_note=(
            "All procedures are recommendations for a human responder; this system does not "
            "execute remediation automatically."
        ),
        summary="Runbook guidance on connection pool exhaustion closely matches observed symptoms.",
        confidence=0.65,
    )


def build_fixture_rca_report() -> RootCauseInvestigationReport:
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


def build_fixture_remediation_report() -> RemediationRecommendationReport:
    return RemediationRecommendationReport(
        recommendations=[
            Recommendation(
                action=(
                    "Pause or reschedule the payment-reconciliation-job outside of peak "
                    "traffic hours until the connection pool sizing is reviewed."
                ),
                reason=(
                    "The reconciliation job's run window overlapped the connection pool "
                    "saturating at 100% utilization; deferring it reduces contention for "
                    "the same limited connections."
                ),
                risk="Low -- scheduling change only, fully reversible.",
                requires_human_approval=True,
            ),
            Recommendation(
                action=(
                    "Add or review the index supporting the reconciliation job's query "
                    "against the transactions table."
                ),
                reason=(
                    "The runbook's Likely Causes section identifies long-running queries "
                    "from missing indexes as a common trigger for pool exhaustion."
                ),
                risk="Medium -- requires a schema review and testing before applying.",
                requires_human_approval=True,
            ),
        ],
        safety_notice=(
            "These are recommendations only. This system does not execute any change "
            "automatically; a human responder must review and approve each action before "
            "it is carried out."
        ),
        summary=(
            "Reschedule the contending batch job and review query indexing to relieve "
            "database connection pool pressure."
        ),
        confidence=0.7,
    )


def build_fixture_incident_report() -> IncidentReport:
    remediation = build_fixture_remediation_report()
    rca = build_fixture_rca_report()
    return IncidentReport(
        incident_id="INC-2026-0912",
        severity="SEV-2",
        service="Payment API",
        impact=(
            "Checkout and payment confirmation requests experienced elevated latency and "
            "intermittent failures; some payment attempts returned HTTP 500 and required "
            "client retry."
        ),
        timeline=[
            TimelineEntry(
                timestamp="2026-09-12T14:08:00Z",
                description="Database connection pool utilization reached 100%.",
                source="Cloud Infrastructure Analyst",
            ),
            TimelineEntry(
                timestamp="2026-09-12T14:10:15Z",
                description="First pod restarted after repeated liveness probe failures.",
                source="Kubernetes Reliability Analyst",
            ),
        ],
        log_findings="HikariCP connection pool timeouts caused HTTP 500 errors.",
        cloud_findings="Database CPU and connection pool utilization both peaked during the incident.",
        kubernetes_findings="4 of 6 pods restarted following liveness probe failures.",
        relevant_runbook="Runbook Likely Causes section matches long-running queries exhausting the pool.",
        root_cause=rca.root_cause,
        alternative_hypotheses=[h.hypothesis for h in rca.alternative_hypotheses],
        confidence=rca.confidence,
        remediation_recommendations=remediation.recommendations,
        human_approval_requirement=(
            "Every recommendation above requires human approval before any action is taken; "
            "this system never executes remediation automatically."
        ),
    )
