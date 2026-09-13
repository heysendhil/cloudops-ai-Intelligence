import type { IncidentSummary, InvestigationJob } from "./types";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function detailToMessage(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

/** Read-only incident metadata (severity, service, environment, symptoms).
 * No investigation is triggered. */
export async function fetchIncidentSummary(
  incidentId: string,
): Promise<IncidentSummary> {
  const response = await fetch(
    `/api/incidents/${encodeURIComponent(incidentId)}`,
  );
  const body = await readJson(response);

  if (!response.ok) {
    throw new ApiError(
      detailToMessage(body, "Could not load this incident."),
      response.status,
    );
  }

  return body as IncidentSummary;
}

/** Starts a CloudOps investigation in the background and returns its job
 * immediately (every task 'pending') -- poll pollInvestigationJob() for
 * real per-agent progress as it happens. Throws only for request-level
 * problems (malformed incident id, network/server error); an unknown
 * incident_id is not an error here -- the job's status simply becomes
 * 'invalid' once polled, with every task still 'pending'. */
export async function startInvestigationJob(
  incidentId: string,
): Promise<InvestigationJob> {
  const response = await fetch(
    `/api/incidents/${encodeURIComponent(incidentId)}/investigations`,
    { method: "POST" },
  );
  const body = await readJson(response);

  if (!response.ok) {
    throw new ApiError(
      detailToMessage(body, "Could not start the investigation."),
      response.status,
    );
  }

  return body as InvestigationJob;
}

/** Fetches the current, real state of a previously-started investigation
 * job -- per-agent status here always reflects actual backend/CrewAI task
 * events, never a client-side simulation. */
export async function pollInvestigationJob(
  incidentId: string,
  jobId: string,
): Promise<InvestigationJob> {
  const response = await fetch(
    `/api/incidents/${encodeURIComponent(incidentId)}/investigations/${encodeURIComponent(jobId)}`,
  );
  const body = await readJson(response);

  if (!response.ok) {
    throw new ApiError(
      detailToMessage(body, "Could not fetch investigation status."),
      response.status,
    );
  }

  return body as InvestigationJob;
}
