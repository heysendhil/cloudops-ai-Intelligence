# Cloud Ops AI Intelligence

An enterprise-oriented, multi-agent system for investigating Cloud and Kubernetes
incidents, built on CrewAI's Agent → Task → Crew → Flow architecture.

> **Status: Architecture & rules phase.** No agents or application code have been
> implemented yet. This repository currently contains only project rules and design
> documentation. See [CLAUDE.md](CLAUDE.md) for the constraints governing implementation.

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
| LLM provider | OpenAI API |
| Testing | pytest |
| Source control | Git |

## Documentation

- [docs/requirements.md](docs/requirements.md) — functional & non-functional requirements, scope
- [docs/architecture.md](docs/architecture.md) — system architecture and data flow
- [docs/agent-design.md](docs/agent-design.md) — per-agent and per-task specification
- [docs/evaluation.md](docs/evaluation.md) — how agent/system output quality is evaluated
- [docs/security.md](docs/security.md) — security, credentials, and safety rules

## Project rules

See [CLAUDE.md](CLAUDE.md) for the constraints that govern all implementation work in this
repository, including the V1 read-only / simulated-data / no-remediation guarantees.

## Getting started

Implementation has not started. Once it does, setup instructions (Python virtualenv,
`pip install`, `npm install`, running FastAPI and Next.js locally, seeding ChromaDB with
simulated runbooks) will be documented here.
