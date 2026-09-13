const SEVERITY_STYLES: Record<string, string> = {
  "SEV-1": "bg-red-500/15 text-red-300 border-red-500/40",
  "SEV-2": "bg-orange-500/15 text-orange-300 border-orange-500/40",
  "SEV-3": "bg-amber-500/15 text-amber-300 border-amber-500/40",
  "SEV-4": "bg-sky-500/15 text-sky-300 border-sky-500/40",
};

const DEFAULT_STYLE = "bg-slate-500/15 text-slate-300 border-slate-500/40";

export function SeverityBadge({ severity }: { severity: string }) {
  const style = SEVERITY_STYLES[severity] ?? DEFAULT_STYLE;
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold tracking-wide ${style}`}
    >
      {severity}
    </span>
  );
}
