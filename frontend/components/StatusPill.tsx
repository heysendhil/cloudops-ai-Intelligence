import type { InvestigationStatus } from "@/lib/types";

const STATUS_STYLES: Record<InvestigationStatus, string> = {
  succeeded: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
  failed: "bg-red-500/15 text-red-300 border-red-500/40",
  invalid: "bg-slate-500/15 text-slate-300 border-slate-500/40",
};

const STATUS_LABELS: Record<InvestigationStatus, string> = {
  succeeded: "Investigation Succeeded",
  failed: "Investigation Failed",
  invalid: "Incident Not Found",
};

export function StatusPill({ status }: { status: InvestigationStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-semibold tracking-wide ${STATUS_STYLES[status]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {STATUS_LABELS[status]}
    </span>
  );
}
