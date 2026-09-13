import type { IncidentSummary } from "@/lib/types";
import { SeverityBadge } from "./SeverityBadge";

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </dt>
      <dd className="mt-1 text-sm text-slate-200">{value}</dd>
    </div>
  );
}

export function IncidentSummaryCard({
  incident,
}: {
  incident: IncidentSummary;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-xs text-slate-500">
            {incident.incident_id}
          </p>
          <h2 className="mt-0.5 text-lg font-semibold text-slate-100">
            {incident.title}
          </h2>
        </div>
        <SeverityBadge severity={incident.severity} />
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Field label="Service" value={incident.service} />
        <Field label="Environment" value={incident.environment} />
        <Field label="Platform" value={incident.platform} />
        <Field label="Record Status" value={incident.status} />
      </dl>

      <div className="mt-5">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Symptoms
        </p>
        <ul className="mt-2 space-y-1.5">
          {incident.symptoms.map((symptom) => (
            <li
              key={symptom}
              className="flex items-start gap-2 text-sm text-slate-300"
            >
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-500" />
              {symptom}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
