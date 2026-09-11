# Agent & Task Design — Cloud Ops AI Intelligence

This document is the authoritative specification for each Agent and its corresponding
Task(s), the Crew that assembles them, and the Flow that orchestrates the Crew. Implement
against this document; if the design changes during implementation, update this document in
the same change.

## 1. Agent roster

Each agent owns exactly one evidence domain or synthesis responsibility. No two agents
should be able to produce overlapping conclusions from the same evidence.

### 1. Log Analyst Agent

- **Role:** Application/system log analyst.
- **Goal:** Identify anomalies, error patterns, and a timeline of relevant events from the
  simulated logs for the incident window.
- **Backstory:** A senior SRE who has spent years reading application and system logs to
  find the first sign of trouble before it becomes an outage.
- **Inputs:** Simulated log fixtures for the incident's affected service(s) and time window.
- **Outputs:** Structured findings — anomalies detected, error signatures, first/last
  occurrence timestamps, an event timeline, and severity assessment per finding.
- **Tools (future):** A read-only log-fixture query tool. No live logging backend access.
- **Explicitly out of scope:** Cloud resource state, Kubernetes object state, remediation.

### 2. Cloud Infrastructure Analyst Agent

- **Role:** Cloud infrastructure analyst.
- **Goal:** Identify anomalies in simulated cloud infrastructure state/metrics (compute,
  networking, load balancing, autoscaling, provider-level events) correlated with the
  incident window.
- **Backstory:** A cloud platform engineer fluent in reading infrastructure telemetry
  across compute, network, and managed services to spot resource exhaustion, config drift,
  and provider-side issues.
- **Inputs:** Simulated cloud-state/metrics fixtures for the incident window.
- **Outputs:** Structured findings — affected resources, metric anomalies, relevant
  provider events, correlation with the incident timeline.
- **Tools (future):** A read-only cloud-fixture query tool. No live cloud API access, no
  credentials.
- **Explicitly out of scope:** Application log content, Kubernetes object state,
  remediation.

### 3. Kubernetes Reliability Analyst Agent

- **Role:** Kubernetes reliability analyst.
- **Goal:** Identify reliability issues in simulated Kubernetes state (pods, deployments,
  nodes, events, resource limits/requests) correlated with the incident window.
- **Backstory:** A platform engineer specializing in Kubernetes who diagnoses
  crash-loops, scheduling failures, resource pressure, and rollout issues.
- **Inputs:** Simulated K8s object/event fixtures (pod status, deployment status, node
  conditions, K8s events) for the affected namespace/workload.
- **Outputs:** Structured findings — affected workloads, pod/deployment/node conditions of
  concern, relevant K8s events, correlation with the incident timeline.
- **Tools (future):** A read-only K8s-fixture query tool. No live `kubectl`/API server
  access, no kubeconfig.
- **Explicitly out of scope:** Cloud provider-level resources, application log content,
  remediation.

### 4. Knowledge/RAG Agent

- **Role:** Incident knowledge retrieval specialist.
- **Goal:** Retrieve relevant historical context — past incidents, runbooks, architecture
  notes — from the ChromaDB knowledge store that may explain or relate to the current
  incident.
- **Backstory:** The team's institutional memory: has read every postmortem and runbook and
  can recall which past incident looked like this one.
- **Inputs:** Incident description/symptoms plus salient details surfaced early in the
  investigation (e.g., affected service name).
- **Outputs:** Ranked list of relevant knowledge base entries with similarity/relevance
  rationale, and a summary of applicable precedent.
- **Tools (future):** ChromaDB retrieval tool. This is the **only** agent permitted to
  query ChromaDB directly (see CLAUDE.md).
- **Explicitly out of scope:** Producing a root cause itself; it supplies context, not
  conclusions.

### 5. Root Cause Investigator Agent

- **Role:** Root cause investigator.
- **Goal:** Synthesize the Log, Cloud Infrastructure, Kubernetes, and Knowledge/RAG
  findings into one or more ranked root-cause hypotheses, each with a confidence level and
  the specific evidence supporting it.
- **Backstory:** A principal engineer who leads incident postmortems and is skilled at
  correlating disparate signals into a coherent causal narrative.
- **Inputs:** Outputs of tasks 1–4 (log, cloud, K8s, knowledge retrieval).
- **Outputs:** Ranked root-cause hypotheses, each with confidence level, supporting
  evidence citations back to the source agent findings, and any open questions/gaps.
- **Tools (future):** None beyond the LLM itself — pure synthesis over prior task outputs.
- **Explicitly out of scope:** Proposing remediation, writing the final report.

### 6. Remediation Advisor Agent

- **Role:** Remediation advisor.
- **Goal:** Given the ranked root-cause hypotheses, propose remediation options ranked by
  expected impact and risk. **Recommendations only — nothing is executed.**
- **Backstory:** A senior SRE who has resolved this class of incident before and knows the
  trade-offs between a quick mitigation and a durable fix.
- **Inputs:** Root Cause Investigator Agent output.
- **Outputs:** Ranked remediation options, each with expected impact, risk level,
  reversibility, and prerequisites. Explicitly labeled as recommendations for human review.
- **Tools (future):** None that can act on infrastructure — advisory text generation only,
  optionally referencing relevant runbook steps retrieved earlier by the Knowledge/RAG
  Agent.
- **Explicitly out of scope:** Executing any action; that capability does not exist in this
  system (see CLAUDE.md, docs/security.md).

### 7. Incident Reporter Agent

- **Role:** Incident reporter.
- **Goal:** Compile all prior task outputs into a single, well-structured, human-readable
  incident report.
- **Backstory:** A technical writer embedded in the SRE team who turns investigation output
  into postmortem-quality documentation.
- **Inputs:** Outputs of all prior tasks (log, cloud, K8s, knowledge, root cause,
  remediation).
- **Outputs:** Final incident report containing: executive summary, incident timeline,
  evidence by domain (log/cloud/K8s), relevant historical precedent, ranked root cause(s),
  ranked remediation recommendations, and open questions/next steps.
- **Tools (future):** None — pure compilation/formatting over prior outputs.
- **Explicitly out of scope:** Introducing new findings not present in upstream task
  outputs.

## 2. Task specification

| # | Task | Agent | Depends on | Expected output |
|---|---|---|---|---|
| 1 | Log Analysis Task | Log Analyst Agent | Incident trigger + log fixtures | Structured log findings |
| 2 | Cloud Infrastructure Analysis Task | Cloud Infrastructure Analyst Agent | Incident trigger + cloud fixtures | Structured cloud findings |
| 3 | Kubernetes Reliability Analysis Task | Kubernetes Reliability Analyst Agent | Incident trigger + K8s fixtures | Structured K8s findings |
| 4 | Knowledge Retrieval Task | Knowledge/RAG Agent | Incident trigger | Ranked relevant knowledge base entries |
| 5 | Root Cause Synthesis Task | Root Cause Investigator Agent | Tasks 1–4 | Ranked root-cause hypotheses w/ evidence |
| 6 | Remediation Recommendation Task | Remediation Advisor Agent | Task 5 | Ranked remediation recommendations |
| 7 | Incident Report Compilation Task | Incident Reporter Agent | Tasks 1–6 | Final structured incident report |

Tasks 1–4 have no interdependency and may run concurrently. Tasks 5, 6, and 7 are strictly
sequential.

## 3. Crew: CloudOps Investigation Crew

- Assembles all 7 agents and their 7 tasks as specified above.
- Process: sequential, with tasks 1–4 eligible for async/parallel execution (final
  CrewAI configuration — e.g., `async_execution=True` on tasks 1–4 — is decided at
  implementation time consistent with this document).
- Context passing: task 5 receives context from tasks 1–4; task 6 receives context from
  task 5; task 7 receives context from tasks 1–6.
- The Crew has no knowledge of *when* or *why* it's invoked — that belongs to the Flow.
- The Crew does not persist output, call FastAPI, or perform any I/O beyond what its tasks'
  tools do (fixture reads, ChromaDB query, OpenAI calls).

## 4. Flow: CloudOps Incident Investigation Flow

Application-level orchestration, responsible for:

1. Accepting a simulated incident trigger.
2. Loading the matching simulated data bundle (logs, cloud state, K8s state).
3. Kicking off the CloudOps Investigation Crew with that context.
4. Applying any post-run routing (e.g., re-running with refined instructions if the Root
   Cause Investigator Agent reports low confidence and insufficient evidence).
5. Persisting the final report and returning it to the FastAPI layer.

The Flow must not perform evidence analysis itself — all reasoning belongs in the Crew's
agents/tasks. The Flow's job is control flow and I/O, not investigation.

## 5. Boundaries checklist (for implementation review)

- [ ] Each agent's tool access matches "Tools (future)" above — no agent has tools outside
      its stated domain.
- [ ] Only the Knowledge/RAG Agent queries ChromaDB.
- [ ] No agent or tool can issue a mutating call to any infrastructure API.
- [ ] The Root Cause Investigator Agent only receives task outputs, never raw fixture data
      directly.
- [ ] The Incident Reporter Agent introduces no new claims beyond upstream task outputs.
- [ ] The Flow contains no direct LLM/Agent calls outside of invoking the Crew.
