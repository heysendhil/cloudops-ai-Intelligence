export function EmptyState({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 px-6 py-14 text-center">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        className="mb-3 h-8 w-8 text-slate-600"
        aria-hidden="true"
      >
        <rect
          x="3.5"
          y="4.5"
          width="17"
          height="15"
          rx="2"
          stroke="currentColor"
          strokeWidth="1.4"
        />
        <path
          d="M3.5 9.5h17"
          stroke="currentColor"
          strokeWidth="1.4"
        />
        <path
          d="M8 14h8"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinecap="round"
        />
      </svg>
      <p className="text-sm font-medium text-slate-300">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-slate-500">{message}</p>
    </div>
  );
}
