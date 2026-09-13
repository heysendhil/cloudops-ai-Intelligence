"""FastAPI integration for the CloudOps Incident Investigation Flow.

Workflow: FastAPI -> CrewAI Flow -> CloudOps Investigation Crew ->
Agents/Tasks -> Final Incident Report -> FastAPI response. This module
only translates between HTTP and the Flow's own result (see app/flow.py);
it performs no investigation logic itself and has no capability to execute
a production change -- V1 remains read-only (see CLAUDE.md,
docs/security.md).
"""

from __future__ import annotations

import json
import os
from pathlib import Path as FilePath

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from app.flow import INCIDENTS_DIR, CloudOpsInvestigationFlow
from app.investigations import get_job, start_investigation
from app.tasks.incident_reporting_task import IncidentReport

router = APIRouter(prefix="/incidents", tags=["incidents"])

# Alphanumeric/dash/underscore only: rejects path-traversal or otherwise
# malformed incident identifiers before they ever reach the Flow (which
# uses this value to build a filesystem path).
INCIDENT_ID_PATTERN = r"^[A-Za-z0-9_-]+$"
JOB_ID_PATTERN = r"^[A-Za-z0-9-]+$"


class IncidentSummary(BaseModel):
    """Read-only incident metadata, straight from the incident record --
    no investigation, no LLM call. Exists so the dashboard can display
    fields (environment, symptoms) that only live on the raw incident
    record, not on the investigation result (see InvestigationResponse)."""

    incident_id: str
    title: str
    severity: str
    service: str
    environment: str
    platform: str
    status: str
    symptoms: list[str] = Field(default_factory=list)


class InvestigationResponse(BaseModel):
    incident_id: str
    status: str = Field(description="One of 'succeeded', 'failed', or 'invalid'.")
    error: str | None = None
    incident_report: IncidentReport | None = None
    requires_human_approval: bool = Field(
        default=True,
        description="Always true: this system never executes remediation automatically.",
    )


class TaskProgressResponse(BaseModel):
    name: str = Field(description="The task's name, e.g. 'Log Analysis Task'.")
    status: str = Field(description="One of 'pending', 'running', 'completed', or 'failed'.")
    finding_summary: str | None = Field(
        default=None,
        description="A real finding from this task's output, once it has completed. "
        "Never populated before the task actually completes.",
    )
    error: str | None = None


class InvestigationJobResponse(BaseModel):
    job_id: str
    incident_id: str
    status: str = Field(description="One of 'running', 'succeeded', 'failed', or 'invalid'.")
    tasks: list[TaskProgressResponse] = Field(
        description="Per-agent status for all 7 pipeline tasks, in execution order. "
        "Reflects real CrewAI task events -- a task not yet reached by the Crew stays "
        "'pending', it is never shown as completed early."
    )
    result: InvestigationResponse | None = None
    error: str | None = None


def _redact_secrets(text: str | None) -> str | None:
    """Strip any configured secret value out of text before it can reach an
    HTTP response, regardless of where in the call stack it originated."""
    if not text:
        return text
    secret = os.environ.get("GOOGLE_API_KEY", "").strip()
    if secret and secret in text:
        text = text.replace(secret, "****")
    return text


@router.get(
    "/{incident_id}",
    response_model=IncidentSummary,
    responses={404: {"description": "No incident record exists for the given incident_id."}},
)
def get_incident_summary(
    incident_id: str = Path(
        ...,
        pattern=INCIDENT_ID_PATTERN,
        description="The incident identifier, e.g. INC-2026-0912.",
    ),
) -> IncidentSummary:
    """Return the incident record's own metadata -- read-only, no
    investigation triggered, no LLM call. Lets the dashboard show incident
    details (e.g. before the user starts an investigation) using the same
    real data/incidents/<id>.json file the Flow itself reads.
    """
    incident_path = FilePath(INCIDENTS_DIR) / f"{incident_id}.json"
    if not incident_path.is_file():
        raise HTTPException(
            status_code=404, detail=f"No incident record found for '{incident_id}'."
        )

    record = json.loads(incident_path.read_text(encoding="utf-8"))
    return IncidentSummary(
        incident_id=record["incident_id"],
        title=record["title"],
        severity=record["severity"],
        service=record["service"]["name"],
        environment=record["environment"],
        platform=record["platform"],
        status=record["status"],
        symptoms=record.get("symptoms", []),
    )


@router.post(
    "/{incident_id}/investigate",
    response_model=InvestigationResponse,
    responses={
        404: {"description": "No incident record exists for the given incident_id."},
        422: {"description": "incident_id is malformed."},
        500: {"description": "The investigation failed or an unexpected error occurred."},
    },
)
def investigate_incident(
    incident_id: str = Path(
        ...,
        pattern=INCIDENT_ID_PATTERN,
        description="The incident identifier, e.g. INC-2026-0912.",
    ),
) -> InvestigationResponse:
    """Run a full CloudOps investigation for one incident and return the
    final report. This call is synchronous and blocking (the underlying
    Crew makes several LLM calls); FastAPI runs sync path operations in a
    threadpool, so it does not block the event loop for other requests.
    """
    try:
        flow = CloudOpsInvestigationFlow()
        result = flow.kickoff(inputs={"incident_id": incident_id})
    except Exception as exc:  # noqa: BLE001 -- truly unexpected; the Flow handles its own failures
        raise HTTPException(
            status_code=500,
            detail=_redact_secrets(f"Unexpected error running the investigation: {exc}"),
        ) from exc

    response = InvestigationResponse(
        incident_id=result["incident_id"],
        status=result["status"],
        error=_redact_secrets(result.get("error")),
        incident_report=result.get("incident_report"),
        requires_human_approval=result.get("requires_human_approval", True),
    )

    if response.status == "invalid":
        raise HTTPException(status_code=404, detail=response.model_dump())

    return response


def _job_to_response(job) -> InvestigationJobResponse:  # noqa: ANN001 -- InvestigationJob, avoids import cycle noise
    result_response = None
    if job.result is not None:
        result_response = InvestigationResponse(
            incident_id=job.result["incident_id"],
            status=job.result["status"],
            error=_redact_secrets(job.result.get("error")),
            incident_report=job.result.get("incident_report"),
            requires_human_approval=job.result.get("requires_human_approval", True),
        )

    return InvestigationJobResponse(
        job_id=job.job_id,
        incident_id=job.incident_id,
        status=job.status,
        tasks=[
            TaskProgressResponse(
                name=t.name,
                status=t.status,
                finding_summary=_redact_secrets(t.finding_summary),
                error=_redact_secrets(t.error),
            )
            for t in job.tasks
        ],
        result=result_response,
        error=_redact_secrets(job.error),
    )


@router.post(
    "/{incident_id}/investigations",
    response_model=InvestigationJobResponse,
    status_code=202,
    responses={422: {"description": "incident_id is malformed."}},
)
def start_incident_investigation(
    incident_id: str = Path(
        ...,
        pattern=INCIDENT_ID_PATTERN,
        description="The incident identifier, e.g. INC-2026-0912.",
    ),
) -> InvestigationJobResponse:
    """Start a CloudOps investigation in the background and return its job
    immediately (all 7 tasks 'pending'). Poll
    GET /incidents/{incident_id}/investigations/{job_id} for real progress
    -- this endpoint does not validate that the incident exists up front
    (that happens inside the Flow, same as POST .../investigate); an
    unknown incident_id simply results in a job whose status becomes
    'invalid' with every task still 'pending', since the Crew never runs.
    """
    job = start_investigation(incident_id)
    return _job_to_response(job)


@router.get(
    "/{incident_id}/investigations/{job_id}",
    response_model=InvestigationJobResponse,
    responses={404: {"description": "No investigation job exists for the given job_id."}},
)
def get_incident_investigation(
    incident_id: str = Path(..., pattern=INCIDENT_ID_PATTERN),
    job_id: str = Path(..., pattern=JOB_ID_PATTERN),
) -> InvestigationJobResponse:
    """Poll the real, current status of a running or finished investigation
    job -- per-task status here always reflects actual CrewAI task events,
    never a simulated timeline."""
    job = get_job(job_id)
    if job is None or job.incident_id != incident_id:
        raise HTTPException(status_code=404, detail=f"No investigation job found for '{job_id}'.")

    return _job_to_response(job)
