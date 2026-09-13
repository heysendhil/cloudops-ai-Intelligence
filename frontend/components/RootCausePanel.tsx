import type { IncidentReport } from "@/lib/types";
import { ConfidenceMeter } from "./ConfidenceMeter";

export function RootCausePanel({ report }: { report: IncidentReport }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <h3 className="text-sm font-semibold text-slate-100">Root Cause</h3>
      <p className="mt-2 text-sm leading-relaxed text-slate-200">
        {report.root_cause}
      </p>

      <div className="mt-4">
        <ConfidenceMeter confidence={report.confidence} />
      </div>

      {report.alternative_hypotheses.length > 0 && (
        <div className="mt-5">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Alternative Hypotheses Considered
          </p>
          <ul className="mt-2 space-y-1.5">
            {report.alternative_hypotheses.map((hypothesis, index) => (
              <li
                key={index}
                className="flex items-start gap-2 text-sm text-slate-400"
              >
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-600" />
                {hypothesis}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
