# CloudOps AI Intelligence — Frontend

The "CloudOps Incident Commander" dashboard for the Cloud Ops AI Intelligence project (see
the [repo root README](../README.md) and [CLAUDE.md](../CLAUDE.md) for the full system).
Next.js 16 (App Router) + TypeScript + Tailwind v4.

## Getting started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) (or whatever port `next dev` picks —
pass `-- --port <n>` to choose one explicitly). The dashboard auto-loads the one simulated
incident in this repo, `INC-2026-0912`, on mount.

The backend must be running separately for the dashboard to show real data — see
[../README.md](../README.md#backend). By default this app talks to
`http://localhost:8000`; override with the `BACKEND_API_URL` environment variable. No
`.env` file is required for local development.

## How it talks to the backend

This app never calls the FastAPI backend directly from the browser. Instead, `app/api/`
holds Next.js Route Handlers that act as a backend-for-frontend (BFF) proxy:

- `GET  /api/incidents/[incidentId]` → incident metadata
- `POST /api/incidents/[incidentId]/investigate` → run a full, blocking investigation
- `POST /api/incidents/[incidentId]/investigations` → start an investigation job
- `GET  /api/incidents/[incidentId]/investigations/[jobId]` → poll job/task progress

This keeps the backend's real URL and any future auth off the client and avoids needing
CORS configuration on the FastAPI side (there is none).

## Structure

- `app/page.tsx` — the dashboard page: incident summary, start/poll an investigation, results
- `app/layout.tsx` — root layout and page metadata
- `app/api/` — the BFF proxy routes described above
- `components/` — presentational pieces: `AgentWorkflow`, `IncidentSummaryCard`,
  `RootCausePanel`, `EvidencePanel`, `RemediationList`, `ApprovalBanner`, `ConfidenceMeter`,
  `SeverityBadge`, `StatusPill`, `ErrorBanner`, `EmptyState`
- `lib/api-client.ts` — typed fetch wrappers around the BFF routes (`ApiError`, etc.)
- `lib/types.ts` — shared TypeScript types mirroring the backend's Pydantic response models

## Testing

```bash
npm test
```

Runs Vitest + Testing Library against `lib/api-client.test.ts` and
`components/AgentWorkflow.test.tsx`. See
[../docs/evaluation-report.md](../docs/evaluation-report.md) for current results as part of
the full project test suite.

## Other scripts

```bash
npm run build   # production build
npm run start   # serve the production build
npm run lint    # eslint
```
