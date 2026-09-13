import type { Recommendation } from "@/lib/types";

function riskStyle(risk: string): string {
  const normalized = risk.toLowerCase();
  if (normalized.includes("high")) return "border-red-500/40 text-red-300 bg-red-500/10";
  if (normalized.includes("medium")) return "border-amber-500/40 text-amber-300 bg-amber-500/10";
  if (normalized.includes("low")) return "border-emerald-500/40 text-emerald-300 bg-emerald-500/10";
  return "border-slate-600/40 text-slate-300 bg-slate-500/10";
}

function RecommendationCard({
  recommendation,
  index,
}: {
  recommendation: Recommendation;
  index: number;
}) {
  return (
    <li className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-slate-100">
          <span className="mr-2 font-mono text-xs text-slate-600">
            {String(index + 1).padStart(2, "0")}
          </span>
          {recommendation.action}
        </p>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-slate-400">
        {recommendation.reason}
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span
          className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${riskStyle(
            recommendation.risk,
          )}`}
        >
          Risk: {recommendation.risk}
        </span>
        {recommendation.requires_human_approval && (
          <span className="inline-flex items-center gap-1 rounded-md border border-sky-500/40 bg-sky-500/10 px-2 py-0.5 text-xs font-medium text-sky-300">
            Requires human approval
          </span>
        )}
      </div>
    </li>
  );
}

export function RemediationList({
  recommendations,
}: {
  recommendations: Recommendation[];
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <h3 className="text-sm font-semibold text-slate-100">
        Remediation Recommendations
      </h3>
      <p className="mt-0.5 text-xs text-slate-500">
        Advisory only -- nothing below is executed automatically.
      </p>
      <ul className="mt-4 space-y-3">
        {recommendations.map((recommendation, index) => (
          <RecommendationCard
            key={index}
            recommendation={recommendation}
            index={index}
          />
        ))}
      </ul>
    </div>
  );
}
