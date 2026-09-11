# Requirements — Cloud Ops AI Intelligence

## 1. Purpose

Give SRE, DevOps, and Platform Engineering teams an AI-assisted first-pass investigation
of a Cloud/Kubernetes incident: what happened, where, probable root cause, and recommended
next steps — produced in minutes from existing telemetry, without granting the system any
ability to act on production infrastructure.

## 2. Personas

- **On-call SRE** — receives an incident report and needs a fast, trustworthy triage
  summary before deciding whether to page others or act.
- **Platform/Kubernetes engineer** — needs cluster-level and infra-level signal correlated
  with application logs, not just raw dashboards.
- **Incident commander / engineering manager** — needs a written incident record (timeline,
  root cause, remediation options) suitable for a postmortem.

## 3. V1 Functional Requirements

1. The system shall accept a simulated incident trigger (e.g., an alert payload) as input.
2. The system shall analyze simulated application/system logs for the affected time window
   and surface anomalies, error patterns, and a timeline of relevant log events.
3. The system shall analyze simulated cloud infrastructure state/metrics (compute,
   networking, load balancing, autoscaling, provider-level events) for anomalies correlated
   with the incident window.
4. The system shall analyze simulated Kubernetes state (pods, deployments, nodes, events,
   resource limits) for reliability issues correlated with the incident window.
5. The system shall retrieve relevant historical context (past incidents, runbooks,
   architecture notes) from a ChromaDB-backed knowledge store.
6. The system shall synthesize findings from logs, cloud, Kubernetes, and knowledge
   retrieval into one or more probable root causes, each with a stated confidence level and
   supporting evidence.
7. The system shall propose remediation recommendations tied to the identified root
   cause(s), ranked by expected impact and risk, **without executing any of them**.
8. The system shall produce a structured, human-readable incident report (executive
   summary, timeline, evidence, root cause, recommended remediation, open questions).
9. The system shall expose the investigation via a FastAPI backend, consumable by a Next.js
   frontend for review by a human operator.
10. The system shall run its investigation as a CrewAI Flow that orchestrates a single
    Crew ("CloudOps Investigation Crew") composed of the seven defined agents and their
    tasks (see docs/agent-design.md).

## 4. V1 Non-Functional Requirements

- **Determinism of scope, not output:** given the same simulated incident fixture, the
  pipeline stages invoked must be the same; LLM narrative output may vary, but the
  underlying evidence gathering must not skip agents.
- **Traceability:** every claim in the final report must be traceable to a specific piece
  of evidence surfaced by one of the analyst agents or the knowledge agent.
- **Auditability:** each Crew run should be able to reconstruct which agent produced which
  finding, and which task outputs fed the root-cause synthesis.
- **Latency:** a single incident investigation should complete within a few minutes on
  simulated fixture data (exact target to be set once implementation exists and can be
  benchmarked).
- **Testability:** every agent and task must be testable against fixture data independent
  of live OpenAI calls where feasible (see docs/evaluation.md).

## 5. Explicit V1 constraints (see also CLAUDE.md, docs/security.md)

- Simulated Cloud/Kubernetes/application data only — no live cloud or cluster connection.
- Read-only system — no mutating action against any infrastructure target.
- No production credentials anywhere in the system or its configuration.
- No automatic remediation execution — recommendations are advisory only, for a human to
  action.

## 6. Out of scope for V1

- Live/production data ingestion of any kind.
- Automated or semi-automated remediation execution (e.g., auto-scaling, restarts, config
  changes).
- Multi-tenant/multi-org support.
- Alerting/paging integrations (PagerDuty, Opsgenie, etc.).
- Fine-tuned or self-hosted models — V1 uses the OpenAI API only.
- Role-based access control beyond basic API auth (see docs/security.md for what V1 does
  include).

## 7. Success Criteria

- All seven agents each produce output that maps to a distinct, non-overlapping
  responsibility (see docs/agent-design.md).
- Given a simulated incident fixture with a known injected root cause, the Root Cause
  Investigator Agent's top hypothesis matches the injected root cause across a benchmark
  suite of scenarios (target rate defined in docs/evaluation.md).
- The Incident Reporter Agent's output is a complete, well-formed report for 100% of
  benchmark runs (no missing required sections).
- No code path exists that can issue a write/mutating call to any infrastructure API.
