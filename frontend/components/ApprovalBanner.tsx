export function ApprovalBanner({ statement }: { statement?: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-sky-500/30 bg-sky-500/10 px-4 py-3">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        className="mt-0.5 h-5 w-5 shrink-0 text-sky-300"
        aria-hidden="true"
      >
        <path
          d="M12 2l7 3v6c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V5l7-3z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path
          d="M9 12.5l2 2 4-4.5"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <div>
        <p className="text-sm font-semibold text-sky-200">
          Human approval required
        </p>
        <p className="mt-0.5 text-sm text-sky-200/80">
          {statement ??
            "This system is read-only and never executes remediation automatically. Every recommendation below requires a human responder to review and approve it before any action is taken."}
        </p>
      </div>
    </div>
  );
}
