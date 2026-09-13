import type { TaskProgress, TaskStatus } from "@/lib/types";

// Maps each pipeline task to the agent name it corresponds to (see
// backend/app/crew.py / docs/agent-design.md) -- purely a display label,
// not additional data.
const AGENT_LABELS: Record<string, string> = {
  "Log Analysis Task": "Log Analyst",
  "Cloud Analysis Task": "Cloud Infrastructure Analyst",
  "Kubernetes Analysis Task": "Kubernetes Reliability Analyst",
  "Knowledge Retrieval Task": "Knowledge/RAG Agent",
  "Root Cause Task": "Root Cause Investigator",
  "Remediation Task": "Remediation Advisor",
  "Incident Report Task": "Incident Reporter",
};

function StatusIcon({ status }: { status: TaskStatus }) {
  if (status === "completed") {
    return (
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-400">
        <svg viewBox="0 0 20 20" fill="none" className="h-3.5 w-3.5" aria-hidden="true">
          <path
            d="M4 10.5l3.5 3.5L16 6"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
    );
  }
  if (status === "failed") {
    return (
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-red-500/15 text-red-400">
        <svg viewBox="0 0 20 20" fill="none" className="h-3.5 w-3.5" aria-hidden="true">
          <path
            d="M5.5 5.5l9 9m0-9l-9 9"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      </span>
    );
  }
  if (status === "running") {
    return (
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-500/15">
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-sky-500/30 border-t-sky-400" />
      </span>
    );
  }
  return (
    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-800">
      <span className="h-2 w-2 rounded-full bg-slate-600" />
    </span>
  );
}

const STATUS_LABEL: Record<TaskStatus, string> = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
};

const STATUS_TEXT_STYLE: Record<TaskStatus, string> = {
  pending: "text-slate-500",
  running: "text-sky-300",
  completed: "text-emerald-300",
  failed: "text-red-300",
};

function AgentRow({ task, isLast }: { task: TaskProgress; isLast: boolean }) {
  const label = AGENT_LABELS[task.name] ?? task.name;

  return (
    <li className="relative flex gap-3.5">
      <div className="flex flex-col items-center">
        <StatusIcon status={task.status} />
        {!isLast && (
          <span
            className={`mt-1 w-px flex-1 ${
              task.status === "completed" ? "bg-emerald-500/30" : "bg-slate-800"
            }`}
          />
        )}
      </div>
      <div className="min-w-0 flex-1 pb-5">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
          <p className="text-sm font-medium text-slate-200">{label}</p>
          <span className={`text-xs font-medium ${STATUS_TEXT_STYLE[task.status]}`}>
            {STATUS_LABEL[task.status]}
          </span>
        </div>
        <p className="text-xs text-slate-600">{task.name}</p>

        {task.status === "completed" && task.finding_summary && (
          <p className="mt-1.5 rounded-md border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-300">
            {task.finding_summary}
          </p>
        )}
        {task.status === "failed" && task.error && (
          <p className="mt-1.5 rounded-md border border-red-500/20 bg-red-500/5 px-3 py-2 text-sm text-red-300">
            {task.error}
          </p>
        )}
      </div>
    </li>
  );
}

export function AgentWorkflow({ tasks }: { tasks: TaskProgress[] }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <h3 className="text-sm font-semibold text-slate-100">
        Investigation Workflow
      </h3>
      <p className="mt-0.5 text-xs text-slate-500">
        Live status for each agent in the CloudOps Investigation Crew.
      </p>
      <ol className="mt-4">
        {tasks.map((task, index) => (
          <AgentRow key={task.name} task={task} isLast={index === tasks.length - 1} />
        ))}
      </ol>
    </div>
  );
}
