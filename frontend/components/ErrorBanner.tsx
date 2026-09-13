export function ErrorBanner({
  title,
  message,
  onRetry,
}: {
  title: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3.5">
      <div className="flex items-start gap-3">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className="mt-0.5 h-5 w-5 shrink-0 text-red-400"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
          <path
            d="M12 8v5"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
          <circle cx="12" cy="16" r="0.9" fill="currentColor" />
        </svg>
        <div>
          <p className="text-sm font-semibold text-red-300">{title}</p>
          <p className="mt-0.5 break-words text-sm text-red-200/80">
            {message}
          </p>
        </div>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="shrink-0 rounded-md border border-red-500/40 px-3 py-1.5 text-xs font-medium text-red-200 transition hover:bg-red-500/15"
        >
          Retry
        </button>
      )}
    </div>
  );
}
