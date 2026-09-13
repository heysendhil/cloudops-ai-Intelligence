import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, pollInvestigationJob, startInvestigationJob } from "./api-client";
import type { InvestigationJob } from "./types";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const RUNNING_JOB: InvestigationJob = {
  job_id: "job-1",
  incident_id: "INC-2026-0912",
  status: "running",
  tasks: [
    { name: "Log Analysis Task", status: "pending", finding_summary: null, error: null },
  ],
  result: null,
  error: null,
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("startInvestigationJob", () => {
  it("POSTs to the investigations endpoint and returns the job", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(RUNNING_JOB, 202));
    vi.stubGlobal("fetch", fetchMock);

    const job = await startInvestigationJob("INC-2026-0912");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/incidents/INC-2026-0912/investigations",
      expect.objectContaining({ method: "POST" }),
    );
    expect(job).toEqual(RUNNING_JOB);
  });

  it("throws ApiError with the backend's detail message on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ detail: "incident_id is malformed" }, 422)),
    );

    await expect(startInvestigationJob("bad id")).rejects.toMatchObject({
      name: "ApiError",
      message: "incident_id is malformed",
      status: 422,
    });
  });

  it("is an instance of ApiError specifically", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: "nope" }, 500)));

    await expect(startInvestigationJob("INC-X")).rejects.toBeInstanceOf(ApiError);
  });
});

describe("pollInvestigationJob", () => {
  it("GETs the specific job and returns its current state", async () => {
    const completedJob: InvestigationJob = { ...RUNNING_JOB, status: "succeeded" };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(completedJob));
    vi.stubGlobal("fetch", fetchMock);

    const job = await pollInvestigationJob("INC-2026-0912", "job-1");

    expect(fetchMock).toHaveBeenCalledWith("/api/incidents/INC-2026-0912/investigations/job-1");
    expect(job.status).toBe("succeeded");
  });

  it("throws ApiError when the job is not found", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ detail: "No investigation job found" }, 404)),
    );

    await expect(pollInvestigationJob("INC-2026-0912", "missing-job")).rejects.toMatchObject({
      status: 404,
    });
  });
});
