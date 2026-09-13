import { NextResponse } from "next/server";

const BACKEND_API_URL = process.env.BACKEND_API_URL ?? "http://localhost:8000";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ incidentId: string; jobId: string }> },
) {
  const { incidentId, jobId } = await params;

  try {
    const backendResponse = await fetch(
      `${BACKEND_API_URL}/incidents/${encodeURIComponent(incidentId)}/investigations/${encodeURIComponent(jobId)}`,
      { cache: "no-store" },
    );
    const body = await backendResponse.json();
    return NextResponse.json(body, { status: backendResponse.status });
  } catch {
    return NextResponse.json(
      { detail: "Could not reach the CloudOps backend. Is it running?" },
      { status: 502 },
    );
  }
}
