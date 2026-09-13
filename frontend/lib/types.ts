// Mirrors backend/app/api/incidents.py and the task report schemas exactly.
// Keep in sync with those Pydantic models -- this file has no fields the
// backend doesn't actually send.

export interface IncidentSummary {
  incident_id: string;
  title: string;
  severity: string;
  service: string;
  environment: string;
  platform: string;
  status: string;
  symptoms: string[];
}

export interface TimelineEntry {
  timestamp: string;
  description: string;
  source: string;
}

export interface Recommendation {
  action: string;
  reason: string;
  risk: string;
  requires_human_approval: true;
}

export interface IncidentReport {
  incident_id: string;
  severity: string;
  service: string;
  impact: string;
  timeline: TimelineEntry[];
  log_findings: string;
  cloud_findings: string;
  kubernetes_findings: string;
  relevant_runbook: string;
  root_cause: string;
  alternative_hypotheses: string[];
  confidence: number;
  remediation_recommendations: Recommendation[];
  human_approval_requirement: string;
}

export type InvestigationStatus = "succeeded" | "failed" | "invalid";

export interface InvestigationResponse {
  incident_id: string;
  status: InvestigationStatus;
  error: string | null;
  incident_report: IncidentReport | null;
  requires_human_approval: boolean;
}

// The 7 CloudOps Investigation Crew agents/tasks, in pipeline order.
// Mirrors backend/app/crew.py's CREW_TASK_NAMES exactly.
export const AGENT_TASK_NAMES = [
  "Log Analysis Task",
  "Cloud Analysis Task",
  "Kubernetes Analysis Task",
  "Knowledge Retrieval Task",
  "Root Cause Task",
  "Remediation Task",
  "Incident Report Task",
] as const;

export type TaskStatus = "pending" | "running" | "completed" | "failed";

export interface TaskProgress {
  name: string;
  status: TaskStatus;
  finding_summary: string | null;
  error: string | null;
}

export type JobStatus = "running" | "succeeded" | "failed" | "invalid";

export interface InvestigationJob {
  job_id: string;
  incident_id: string;
  status: JobStatus;
  tasks: TaskProgress[];
  result: InvestigationResponse | null;
  error: string | null;
}
