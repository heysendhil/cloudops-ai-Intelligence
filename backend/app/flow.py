"""CloudOps Incident Investigation Flow.

Per docs/architecture.md: application-level orchestration only. This Flow
owns the execution order -- receiving the incident trigger, validating it,
loading its data, kicking off the CloudOps Investigation Crew, evaluating
the Crew's result, handling failures, and producing the final result. It
performs no evidence analysis of its own (no LLM calls, no log/metric/K8s
parsing, no synthesis) -- all reasoning belongs to the Crew's agents/tasks
(see CLAUDE.md: "Do not duplicate Crew responsibilities"). V1 remains
read-only: this Flow has no capability to execute a production change, and
every remediation recommendation in its result still requires human
approval (guaranteed independently by Recommendation.requires_human_approval
being typed Literal[True] -- see app/tasks/remediation_recommendation_task.py).
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from crewai.flow.flow import Flow, FlowState, listen, or_, router, start

from app.crew import build_cloudops_investigation_crew

REPO_ROOT = Path(__file__).resolve().parents[2]
INCIDENTS_DIR = REPO_ROOT / "data" / "incidents"


class InvestigationStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    INVALID = "invalid"
    LOADED = "loaded"
    CREW_RUNNING = "crew_running"
    CREW_COMPLETED = "crew_completed"
    CREW_FAILED = "crew_failed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class CloudOpsInvestigationState(FlowState):
    incident_id: str = ""
    severity: str = ""
    service: str = ""
    impact: str = ""
    status: InvestigationStatus = InvestigationStatus.PENDING
    error: str | None = None
    incident_report: dict[str, Any] | None = None


class CloudOpsInvestigationFlow(Flow[CloudOpsInvestigationState]):
    """Owns the application-level execution order for one incident
    investigation. Trigger with `.kickoff(inputs={"incident_id": "..."})`.
    """

    # 1. Receive incident ID -- incident_id is populated on self.state from
    # kickoff(inputs=...) before this (or any) method runs.
    @start()
    def receive_incident(self) -> None:
        self.state.incident_id = self.state.incident_id.strip()
        self.state.status = InvestigationStatus.PENDING

    # 2. Validate incident
    @router(receive_incident)
    def validate_incident(self) -> str:
        if not self.state.incident_id:
            self.state.status = InvestigationStatus.INVALID
            self.state.error = "No incident_id was provided."
            return "invalid"

        if not self._incident_path().is_file():
            self.state.status = InvestigationStatus.INVALID
            self.state.error = (
                f"No incident record found for '{self.state.incident_id}' at "
                f"{self._incident_path()}."
            )
            return "invalid"

        self.state.status = InvestigationStatus.VALIDATED
        return "valid"

    # 3. Load incident data -- plain file I/O only; no analysis, no LLM call.
    @listen("valid")
    def load_incident_data(self) -> None:
        record = json.loads(self._incident_path().read_text(encoding="utf-8"))
        self.state.severity = record["severity"]
        self.state.service = record["service"]["name"]
        self.state.impact = record["impact"]["description"]
        self.state.status = InvestigationStatus.LOADED

    # 4. Start CloudOps Investigation Crew
    @listen(load_incident_data)
    def run_investigation_crew(self) -> None:
        self.state.status = InvestigationStatus.CREW_RUNNING
        try:
            crew = build_cloudops_investigation_crew(
                incident_id=self.state.incident_id,
                severity=self.state.severity,
                service=self.state.service,
                impact=self.state.impact,
            )
            result = crew.kickoff()
        except Exception as exc:  # noqa: BLE001 -- any crew-execution failure is handled, not raised
            self.state.status = InvestigationStatus.CREW_FAILED
            self.state.error = f"{type(exc).__name__}: {exc}"
            return

        if result.pydantic is None:
            self.state.status = InvestigationStatus.CREW_FAILED
            self.state.error = "Crew completed but produced no structured incident report."
            return

        self.state.incident_report = result.pydantic.model_dump(mode="json")
        self.state.status = InvestigationStatus.CREW_COMPLETED

    # 5. Evaluate Crew result
    @router(run_investigation_crew)
    def evaluate_crew_result(self) -> str:
        if self.state.status == InvestigationStatus.CREW_FAILED:
            return "failed"

        report = self.state.incident_report or {}
        missing = [
            field
            for field in ("root_cause", "remediation_recommendations", "incident_id")
            if not report.get(field)
        ]
        if missing:
            self.state.status = InvestigationStatus.CREW_FAILED
            self.state.error = f"Incident report is missing required section(s): {missing}."
            return "failed"

        return "succeeded"

    # 6. Handle failures + 7. Produce final investigation result: one
    # terminal step reached from every path (invalid incident, crew
    # failure, or success), so the Flow never ends without a well-formed
    # result. Deliberately a single method (not separate per-branch
    # listeners on the same trigger label) so there is no ordering
    # ambiguity about which listener sets the final status first.
    @listen(or_("invalid", "failed", "succeeded"))
    def produce_final_result(self) -> dict[str, Any]:
        # Kept distinct (not both collapsed into "failed"): callers -- e.g.
        # the FastAPI layer, see app/api/incidents.py -- need to tell "no
        # such incident" (a 404-shaped, client-facing condition) apart from
        # "the investigation itself failed" (a 500-shaped, server-side one)
        # without parsing the error message.
        if self.state.status == InvestigationStatus.INVALID:
            pass  # already InvestigationStatus.INVALID
        elif self.state.status == InvestigationStatus.CREW_FAILED:
            self.state.status = InvestigationStatus.FAILED
        else:
            self.state.status = InvestigationStatus.SUCCEEDED

        return {
            "incident_id": self.state.incident_id,
            "status": self.state.status.value,
            "error": self.state.error,
            "incident_report": self.state.incident_report,
            # 8. Require human approval for production remediation: this Flow
            # has no ability to execute any change (V1 is read-only -- see
            # CLAUDE.md, docs/security.md), and every recommendation the Crew
            # produces already independently requires human approval
            # (Recommendation.requires_human_approval is Literal[True]).
            # Restated here for the caller's convenience.
            "requires_human_approval": True,
        }

    def _incident_path(self) -> Path:
        return INCIDENTS_DIR / f"{self.state.incident_id}.json"
