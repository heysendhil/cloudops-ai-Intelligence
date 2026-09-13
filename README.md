# Cloud Ops AI Intelligence

An enterprise-oriented, multi-agent system for investigating Cloud and Kubernetes
incidents, built on CrewAI's Agent → Task → Crew → Flow architecture.

> **Status: Implemented (V1).** All 7 agents, their tasks, the CloudOps Investigation
> Crew, the end-to-end Flow, the FastAPI backend, the Next.js dashboard, and the RAG
> knowledge layer are built and tested against the simulated incident INC-2026-0912. See
> [CLAUDE.md](CLAUDE.md) for the constraints governing implementation and
> [docs/evaluation-report.md](docs/evaluation-report.md) for the current full test-suite
> results.

## What it does (V1 scope)

Given a simulated Cloud/Kubernetes incident, a crew of specialized AI agents investigates
logs, cloud infrastructure state, and Kubernetes reliability signals, cross-references a
knowledge base of runbooks and past incidents, determines a probable root cause, proposes
(but never executes) remediation steps, and produces a structured incident report.

V1 is intentionally constrained:

- **Simulated data only** — no connection to real cloud accounts or clusters.
- **Read-only** — no mutating actions against any infrastructure, simulated or real.
- **No production credentials** — nothing in this repo talks to production systems.
- **No automatic remediation** — recommendations only; a human acts on them.

## Architecture

```
CrewAI
  ├── Agents   — 7 specialized investigators
  ├── Tasks    — one clearly-scoped responsibility per agent
  ├── Crew     — CloudOps Investigation Crew
  └── Flow     — application-level incident orchestration
```

The seven agents:

1. Log Analyst Agent
2. Cloud Infrastructure Analyst Agent
3. Kubernetes Reliability Analyst Agent
4. Knowledge/RAG Agent
5. Root Cause Investigator Agent
6. Remediation Advisor Agent
7. Incident Reporter Agent

Full design: [docs/architecture.md](docs/architecture.md) · [docs/agent-design.md](docs/agent-design.md)

## Tech stack

| Layer | Technology |
|---|---|
| Agent orchestration | CrewAI |
| Backend API | FastAPI (Python 3.11) |
| Frontend | Next.js + TypeScript |
| Knowledge store | ChromaDB |
| LLM provider | Google Gemini API (`GOOGLE_API_KEY`) |
| Testing | pytest (backend), Vitest (frontend) |
| Source control | Git |

## Documentation

- [docs/requirements.md](docs/requirements.md) — functional & non-functional requirements, scope
- [docs/architecture.md](docs/architecture.md) — system architecture and data flow
- [docs/agent-design.md](docs/agent-design.md) — per-agent and per-task specification
- [docs/evaluation.md](docs/evaluation.md) — how agent/system output quality is evaluated
- [docs/evaluation-report.md](docs/evaluation-report.md) — generated PASS/FAIL results from the latest full test-suite run
- [docs/security.md](docs/security.md) — security, credentials, and safety rules

## Project rules

See [CLAUDE.md](CLAUDE.md) for the constraints that govern all implementation work in this
repository, including the V1 read-only / simulated-data / no-remediation guarantees.

## Getting started

### Backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # then set GOOGLE_API_KEY in it
cd backend
uvicorn app.main:app --reload --port 8000
```
Health check: `GET http://localhost:8000/health`. Interactive API docs: `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```
Talks to the backend at `http://localhost:8000` by default (override with the `BACKEND_API_URL` env var). No `.env` file is required.

### The one simulated incident

The only incident record in this repo is `INC-2026-0912` (`data/incidents/`, `data/logs/`,
`data/metrics/`, `data/kubernetes/`, `data/runbooks/`). Trigger an investigation with:
```bash
curl -X POST http://localhost:8000/incidents/INC-2026-0912/investigate
```
or from the dashboard, which loads it automatically.

### Tests

```bash
# Structural + adversarial suite (fast, no API key needed, ~11s):
CREWAI_TRACING_ENABLED=false pytest -q

# Also run the live-LLM evaluations against a real Gemini model (needs
# GOOGLE_API_KEY; consumes real, often quota-limited, API usage):
CREWAI_TRACING_ENABLED=false pytest --run-live -q

# Frontend:
cd frontend && npm test
```
Live-LLM evaluations (`tests/evaluation/`) are marked `live_llm` and skipped by default —
see [docs/evaluation.md](docs/evaluation.md) and
[docs/evaluation-report.md](docs/evaluation-report.md) for details.
