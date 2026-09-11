# CLAUDE.md — Project Rules for Cloud Ops AI Intelligence

This file governs how Claude Code (and any implementation agent) works in this repository.
It is binding for all future sessions. If a request conflicts with this file, follow this
file and flag the conflict to the user.

## What this project is

Cloud Ops AI Intelligence is an enterprise-oriented multi-agent system that investigates
Cloud/Kubernetes incidents. It is built on CrewAI using the mandatory layered architecture:

```
CrewAI
  ├── Agents   — specialized investigators (Log, Cloud, K8s, RAG, Root Cause, Remediation, Reporter)
  ├── Tasks    — one clearly-scoped responsibility per agent
  ├── Crew     — "CloudOps Investigation Crew" coordinates agents + tasks
  └── Flow     — application-level orchestration of an end-to-end incident investigation
```

Full details: [docs/architecture.md](docs/architecture.md) and [docs/agent-design.md](docs/agent-design.md).

## Non-negotiable V1 constraints

These apply to every change, in every session, without exception:

1. **Simulated data only.** V1 never connects to a real cloud account, real Kubernetes
   cluster, or real log/metrics backend. All logs, cloud telemetry, and K8s state are
   fixtures/simulators checked into the repo or generated locally.
2. **Read-only.** No component may issue a mutating call against any cloud/K8s/infra API,
   simulated or real, beyond reading state. There is no "apply," "delete," "scale," or
   "restart" action anywhere in V1.
3. **No production credentials.** No `.env`, config file, or code may reference real cloud
   account credentials, kubeconfigs pointing at real clusters, or production API keys.
   Only the OpenAI API key (for LLM calls) and local ChromaDB are real integrations.
4. **No automatic remediation execution.** The Remediation Advisor Agent may only
   *recommend* actions in a report. Nothing in the system executes a remediation. This is
   an architectural rule, not just a prompt instruction — do not wire up any tool that can
   act on infrastructure.
5. **Do not implement agents/application code until explicitly asked.** The current phase
   is architecture and documentation only (see docs/ below). Do not scaffold `agents.py`,
   `tasks.py`, `crew.py`, `flow.py`, FastAPI routes, or the Next.js app until a future
   request explicitly asks for implementation.

## Architecture rules

- Every agent must map to a clearly defined responsibility and produce a task output that
  the next stage in the pipeline consumes. No agent may silently duplicate another agent's
  responsibility (see docs/agent-design.md for the exact boundaries).
- The Agent → Task → Crew → Flow layering must stay explicit in code once implementation
  starts: Agents and Tasks are defined independently, assembled into the Crew, and the Crew
  is invoked from within a Flow that owns application-level control (triggers, branching,
  persistence, API exposure). Do not collapse these layers (e.g., no ad-hoc LLM calls from
  the Flow that bypass the Crew/Task abstraction).
- The Knowledge/RAG Agent is the only agent permitted to query ChromaDB. Other agents that
  need historical context go through it rather than querying the vector store directly.

## Tech stack (do not add to this without discussion)

Python 3.11, CrewAI, FastAPI, Next.js, TypeScript, ChromaDB, OpenAI API, pytest, Git.
Do not install additional frameworks, agent libraries, vector stores, or cloud SDKs without
explicit user approval — see "Do not install unnecessary dependencies" below.

## Working conventions

- **Do not install unnecessary dependencies.** Only add a package when a concrete,
  requested piece of work needs it, and prefer the libraries already listed above.
- **Docs are source of truth for scope.** Before implementing any agent, task, crew, or
  flow, check docs/agent-design.md and docs/architecture.md for the agreed responsibilities
  and update the docs first if the design changes.
- **Tests accompany implementation.** Once application code exists, new agents/tasks/flows
  land with pytest coverage (see docs/evaluation.md for what "coverage" means for
  LLM-driven components).
- **Security review by default.** Any change touching credentials, API auth, data
  ingestion, or the RAG store should be checked against docs/security.md before merging.
- **No emojis** in code, docs, or commit messages unless explicitly requested.
