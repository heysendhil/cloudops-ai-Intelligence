"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  ApiError,
  fetchIncidentSummary,
  pollInvestigationJob,
  startInvestigationJob,
} from "@/lib/api-client";
import type { IncidentSummary, InvestigationJob } from "@/lib/types";

import { AgentWorkflow } from "@/components/AgentWorkflow";
import { ApprovalBanner } from "@/components/ApprovalBanner";
import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";
import { EvidencePanel } from "@/components/EvidencePanel";
import { IncidentSummaryCard } from "@/components/IncidentSummaryCard";
import { RemediationList } from "@/components/RemediationList";
import { RootCausePanel } from "@/components/RootCausePanel";
import { StatusPill } from "@/components/StatusPill";

const DEFAULT_INCIDENT_ID = "INC-2026-0912";
const POLL_INTERVAL_MS = 1200;

type LoadState = "idle" | "loading" | "error";

export default function Dashboard() {
  const [incidentIdInput, setIncidentIdInput] = useState(DEFAULT_INCIDENT_ID);

  const [summary, setSummary] = useState<IncidentSummary | null>(null);
  const [summaryState, setSummaryState] = useState<LoadState>("idle");
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const [job, setJob] = useState<InvestigationJob | null>(null);
  const [jobRequestState, setJobRequestState] = useState<LoadState>("idle");
  const [jobRequestError, setJobRequestError] = useState<string | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const loadIncident = useCallback(
    async (incidentId: string) => {
      stopPolling();
      setSummaryState("loading");
      setSummaryError(null);
      setSummary(null);
      setJob(null);
      setJobRequestState("idle");
      setJobRequestError(null);

      try {
        const result = await fetchIncidentSummary(incidentId);
        setSummary(result);
        setSummaryState("idle");
      } catch (error) {
        setSummaryError(
          error instanceof ApiError ? error.message : "Could not reach the CloudOps backend.",
        );
        setSummaryState("error");
      }
    },
    [stopPolling],
  );

  useEffect(() => {
    // Load the golden-scenario incident on first render for convenience;
    // the operator can still look up a different incident_id below.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadIncident(DEFAULT_INCIDENT_ID);
  }, [loadIncident]);

  useEffect(() => stopPolling, [stopPolling]);

  function pollUntilDone(incidentId: string, jobId: string) {
    pollTimerRef.current = setTimeout(async () => {
      try {
        const latest = await pollInvestigationJob(incidentId, jobId);
        setJob(latest);
        if (latest.status === "running") {
          pollUntilDone(incidentId, jobId);
        }
      } catch (error) {
        setJobRequestError(
          error instanceof ApiError ? error.message : "Could not reach the CloudOps backend.",
        );
        setJobRequestState("error");
      }
    }, POLL_INTERVAL_MS);
  }

  async function handleStartInvestigation() {
    if (!summary) return;
    stopPolling();
    setJobRequestState("loading");
    setJobRequestError(null);
    setJob(null);

    try {
      const started = await startInvestigationJob(summary.incident_id);
      setJob(started);
      setJobRequestState("idle");
      if (started.status === "running") {
        pollUntilDone(summary.incident_id, started.job_id);
      }
    } catch (error) {
      setJobRequestError(
        error instanceof ApiError ? error.message : "Could not reach the CloudOps backend.",
      );
      setJobRequestState("error");
    }
  }

  const investigationResult = job?.result ?? null;

  return (
    <div className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-400">
            CloudOps AI Intelligence
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-100">
            AI Investigation Dashboard
          </h1>
        </div>
        <form
          className="flex items-center gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            void loadIncident(incidentIdInput.trim());
          }}
        >
          <input
            value={incidentIdInput}
            onChange={(event) => setIncidentIdInput(event.target.value)}
            placeholder="INC-2026-0912"
            spellCheck={false}
            className="w-44 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-sm text-slate-200 placeholder:text-slate-600 focus:border-sky-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={summaryState === "loading" || !incidentIdInput.trim()}
            className="rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Load Incident
          </button>
        </form>
      </header>

      <main className="space-y-6">
        {summaryState === "loading" && (
          <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-5 py-6 text-sm text-slate-400">
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-600 border-t-sky-400" />
            Loading incident record&hellip;
          </div>
        )}

        {summaryState === "error" && summaryError && (
          <ErrorBanner
            title="Could not load incident"
            message={summaryError}
            onRetry={() => void loadIncident(incidentIdInput.trim())}
          />
        )}

        {summaryState === "idle" && !summary && (
          <EmptyState
            title="No incident loaded"
            message="Enter an incident ID above and click Load Incident to begin."
          />
        )}

        {summary && (
          <>
            <IncidentSummaryCard incident={summary} />

            <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 px-5 py-4">
              <div>
                <p className="text-sm font-medium text-slate-200">
                  Run the CloudOps Investigation Crew
                </p>
                <p className="mt-0.5 text-xs text-slate-500">
                  Seven AI agents will analyze logs, cloud metrics, Kubernetes
                  state, and runbook knowledge to determine the root cause.
                </p>
              </div>
              <button
                type="button"
                onClick={() => void handleStartInvestigation()}
                disabled={jobRequestState === "loading" || job?.status === "running"}
                className="shrink-0 rounded-md bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {jobRequestState === "loading" || job?.status === "running"
                  ? "Investigating…"
                  : "Start Investigation"}
              </button>
            </div>

            {jobRequestState === "error" && jobRequestError && (
              <ErrorBanner
                title="Investigation request failed"
                message={jobRequestError}
                onRetry={() => void handleStartInvestigation()}
              />
            )}

            {jobRequestState === "idle" && !job && (
              <EmptyState
                title="Investigation not yet started"
                message="Click Start Investigation to run the CloudOps Investigation Crew against this incident."
              />
            )}

            {job && (
              <div className="space-y-6">
                {job.status !== "running" && (
                  <div className="flex items-center justify-between">
                    <StatusPill status={job.status} />
                  </div>
                )}

                <AgentWorkflow tasks={job.tasks} />

                {job.status !== "running" && job.status !== "succeeded" && (
                  <ErrorBanner
                    title={job.status === "invalid" ? "Incident not found" : "Investigation failed"}
                    message={job.error ?? "The investigation did not complete successfully."}
                  />
                )}

                {job.status === "succeeded" && investigationResult?.incident_report && (
                  <>
                    <RootCausePanel report={investigationResult.incident_report} />
                    <EvidencePanel report={investigationResult.incident_report} />
                    <ApprovalBanner
                      statement={investigationResult.incident_report.human_approval_requirement}
                    />
                    {investigationResult.incident_report.remediation_recommendations.length > 0 ? (
                      <RemediationList
                        recommendations={
                          investigationResult.incident_report.remediation_recommendations
                        }
                      />
                    ) : (
                      <EmptyState
                        title="No remediation recommendations"
                        message="The investigation did not produce any remediation recommendations."
                      />
                    )}
                  </>
                )}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
