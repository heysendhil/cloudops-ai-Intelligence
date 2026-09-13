function bandFor(confidence: number): {
  label: string;
  bar: string;
  text: string;
} {
  if (confidence >= 0.7) {
    return { label: "High", bar: "bg-emerald-400", text: "text-emerald-300" };
  }
  if (confidence >= 0.4) {
    return { label: "Moderate", bar: "bg-amber-400", text: "text-amber-300" };
  }
  return { label: "Low", bar: "bg-red-400", text: "text-red-300" };
}

export function ConfidenceMeter({ confidence }: { confidence: number }) {
  const pct = Math.round(Math.max(0, Math.min(1, confidence)) * 100);
  const band = bandFor(confidence);

  return (
    <div className="w-full">
      <div className="mb-1.5 flex items-baseline justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
          Confidence
        </span>
        <span className={`text-sm font-semibold ${band.text}`}>
          {pct}% &middot; {band.label}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full ${band.bar} transition-[width] duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
