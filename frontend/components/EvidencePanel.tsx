import type { IncidentReport } from "@/lib/types";

function FindingCard({
  label,
  text,
}: {
  label: string;
  text: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-1.5 text-sm leading-relaxed text-slate-300">{text}</p>
    </div>
  );
}

function formatTimestamp(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  return Number.isNaN(date.getTime())
    ? isoTimestamp
    : date.toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
}

export function EvidencePanel({ report }: { report: IncidentReport }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <h3 className="text-sm font-semibold text-slate-100">Evidence</h3>
      <p className="mt-0.5 text-xs text-slate-500">
        Findings from each analyst agent, and the runbook guidance the
        investigation retrieved.
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <FindingCard label="Log Findings" text={report.log_findings} />
        <FindingCard label="Cloud Findings" text={report.cloud_findings} />
        <FindingCard
          label="Kubernetes Findings"
          text={report.kubernetes_findings}
        />
        <FindingCard label="Relevant Runbook" text={report.relevant_runbook} />
      </div>

      {report.timeline.length > 0 && (
        <div className="mt-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Timeline
          </p>
          <ol className="mt-2.5 space-y-3 border-l border-slate-800 pl-4">
            {report.timeline.map((entry, index) => (
              <li key={`${entry.timestamp}-${index}`} className="relative">
                <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full border-2 border-slate-950 bg-sky-500" />
                <p className="font-mono text-xs text-slate-500">
                  {formatTimestamp(entry.timestamp)}
                </p>
                <p className="mt-0.5 text-sm text-slate-300">
                  {entry.description}
                </p>
                <p className="mt-0.5 text-xs text-slate-600">
                  Source: {entry.source}
                </p>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
