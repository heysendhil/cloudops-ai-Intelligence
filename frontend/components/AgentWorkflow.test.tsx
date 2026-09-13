import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AgentWorkflow } from "./AgentWorkflow";
import type { TaskProgress } from "@/lib/types";

const ALL_PENDING: TaskProgress[] = [
  { name: "Log Analysis Task", status: "pending", finding_summary: null, error: null },
  { name: "Cloud Analysis Task", status: "pending", finding_summary: null, error: null },
  { name: "Kubernetes Analysis Task", status: "pending", finding_summary: null, error: null },
  { name: "Knowledge Retrieval Task", status: "pending", finding_summary: null, error: null },
  { name: "Root Cause Task", status: "pending", finding_summary: null, error: null },
  { name: "Remediation Task", status: "pending", finding_summary: null, error: null },
  { name: "Incident Report Task", status: "pending", finding_summary: null, error: null },
];

describe("AgentWorkflow", () => {
  it("renders all 7 agents by their display name", () => {
    render(<AgentWorkflow tasks={ALL_PENDING} />);

    expect(screen.getByText("Log Analyst")).toBeInTheDocument();
    expect(screen.getByText("Cloud Infrastructure Analyst")).toBeInTheDocument();
    expect(screen.getByText("Kubernetes Reliability Analyst")).toBeInTheDocument();
    expect(screen.getByText("Knowledge/RAG Agent")).toBeInTheDocument();
    expect(screen.getByText("Root Cause Investigator")).toBeInTheDocument();
    expect(screen.getByText("Remediation Advisor")).toBeInTheDocument();
    expect(screen.getByText("Incident Reporter")).toBeInTheDocument();
  });

  it("shows every agent as Pending before anything has run, with no findings", () => {
    render(<AgentWorkflow tasks={ALL_PENDING} />);

    expect(screen.getAllByText("Pending")).toHaveLength(7);
    expect(screen.queryByText("Running")).not.toBeInTheDocument();
    expect(screen.queryByText("Completed")).not.toBeInTheDocument();
    expect(screen.queryByText("Failed")).not.toBeInTheDocument();
  });

  it("shows Running for a task currently in progress", () => {
    const tasks = ALL_PENDING.map((t, i) =>
      i === 0 ? { ...t, status: "running" as const } : t,
    );

    render(<AgentWorkflow tasks={tasks} />);

    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(screen.getAllByText("Pending")).toHaveLength(6);
  });

  it("shows a real finding only for a task that actually completed", () => {
    const tasks = ALL_PENDING.map((t, i) =>
      i === 0
        ? {
            ...t,
            status: "completed" as const,
            finding_summary: "Database connection pool exhaustion detected.",
          }
        : t,
    );

    render(<AgentWorkflow tasks={tasks} />);

    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(
      screen.getByText("Database connection pool exhaustion detected."),
    ).toBeInTheDocument();
    // the other 6 pending agents must show no finding text at all
    expect(screen.getAllByText("Pending")).toHaveLength(6);
  });

  it("never renders a finding for a pending or running task, even if one were present in the data", () => {
    // A defensive case: if the backend ever sent a stray finding_summary on
    // a non-completed task, the UI must still not display it as a real
    // result -- only 'completed' tasks may show their finding.
    const tasks: TaskProgress[] = [
      {
        name: "Log Analysis Task",
        status: "running",
        finding_summary: "should not be shown",
        error: null,
      },
    ];

    render(<AgentWorkflow tasks={tasks} />);

    expect(screen.queryByText("should not be shown")).not.toBeInTheDocument();
  });

  it("shows the real error only for a task that actually failed", () => {
    const tasks = ALL_PENDING.map((t, i) =>
      i === 1 ? { ...t, status: "failed" as const, error: "Tool execution failed." } : t,
    );

    render(<AgentWorkflow tasks={tasks} />);

    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText("Tool execution failed.")).toBeInTheDocument();
  });

  it("renders nothing extra for an empty task list", () => {
    render(<AgentWorkflow tasks={[]} />);

    expect(screen.getByText("Investigation Workflow")).toBeInTheDocument();
    expect(screen.queryByText("Pending")).not.toBeInTheDocument();
  });
});
