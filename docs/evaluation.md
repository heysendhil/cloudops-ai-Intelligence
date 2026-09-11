# Evaluation — Cloud Ops AI Intelligence

This document defines how the quality of agent, task, crew, and flow output is evaluated.
LLM-driven components cannot be verified with plain assert-equal tests alone, so evaluation
combines deterministic checks (pytest) with scenario-based, rubric-scored checks.

## 1. Evaluation levels

| Level | What it checks | How |
|---|---|---|
| Unit | Individual task's structural output (required fields present, correct types) | pytest, schema validation |
| Component | A single agent's findings against a known-injected fixture anomaly | pytest + fixture-based scenario, LLM-as-judge or rule-based assertions |
| Integration | Crew end-to-end: do tasks 1–7 all execute and hand off context correctly | pytest against the CrewAI Crew with simulated data, mocked/recorded LLM calls where feasible |
| System | Flow end-to-end via FastAPI: trigger → report | pytest + FastAPI test client against simulated incident fixtures |
| Scenario/benchmark | Root cause accuracy, report completeness, remediation soundness across a suite of simulated incidents | Golden scenario suite (see §3) |

## 2. Structural (deterministic) checks

For every task output:

- Required fields are present (per docs/agent-design.md expected outputs).
- Root cause hypotheses include a confidence level and at least one evidence citation.
- Remediation recommendations include impact, risk, and reversibility.
- The final incident report contains every required section (executive summary, timeline,
  evidence by domain, precedent, root cause, remediation, open questions).
- No task output contains a call to, or reference to, a mutating infrastructure action
  (regex/keyword guard as a defense-in-depth check, in addition to the architectural
  guarantee that no such tool exists — see docs/security.md).

These are enforced with pytest and run on every change once implementation exists.

## 3. Golden scenario suite

A set of simulated incident scenarios, each with:

- A fixture bundle (logs, cloud state, K8s state) with a deliberately injected root cause
  (e.g., "node disk pressure caused pod evictions causing 5xx errors").
- The expected/known root cause, for scoring the Root Cause Investigator Agent.
- At least one relevant knowledge-base entry seeded in ChromaDB, for scoring the
  Knowledge/RAG Agent's retrieval relevance.

Minimum V1 scenario set (to be built alongside first implementation, not now):

1. Kubernetes pod crash-loop due to misconfiguration (config/deployment issue only).
2. Node resource pressure causing evictions and cascading application errors.
3. Cloud-side networking/load-balancer misconfiguration causing latency/availability drop.
4. Autoscaling failure leading to resource exhaustion under load.
5. A "noisy but benign" scenario with anomalies that should *not* be flagged as the root
   cause, to check for false positives.

## 4. Metrics

- **Root cause accuracy:** top-ranked hypothesis matches the scenario's injected root cause
  (exact match or human-graded equivalence). Target and measurement cadence to be set once
  a working baseline exists.
- **Evidence traceability:** percentage of root-cause/remediation claims that cite specific
  evidence from an upstream task output (target: 100% — no unsupported claims).
- **Retrieval relevance:** whether the Knowledge/RAG Agent surfaces the seeded relevant
  entry for scenarios that have one.
- **Report completeness:** percentage of benchmark runs producing a fully-sectioned report
  (target: 100%).
- **False positive rate:** rate at which the "noisy but benign" scenario is incorrectly
  diagnosed with a specific root cause instead of correctly reporting low confidence /
  insufficient evidence.
- **Latency and cost:** wall-clock time and OpenAI token cost per investigation, tracked
  once implementation exists, primarily to catch regressions rather than hit a fixed target
  in V1.

## 5. LLM-as-judge usage

Where deterministic assertions are insufficient (e.g., judging whether a root-cause
narrative is coherent and well-supported), an LLM-as-judge rubric may be used, scoring on:

- Coherence — does the narrative logically follow from the cited evidence?
- Groundedness — does it avoid claims unsupported by upstream task outputs?
- Actionability — are remediation recommendations specific enough to act on?

LLM-as-judge results supplement, never replace, the structural pytest checks in §2.

## 6. Regression policy

Any change to an agent's prompt/goal, a task's description/expected output, the Crew's
process, or the Flow's routing logic must be re-run against the full golden scenario suite
before merging, once that suite and implementation exist. A regression in root cause
accuracy or report completeness blocks the change.

## 7. What this document does not cover

- Live/production evaluation — out of scope until V1 constraints (simulated data,
  read-only) are revisited by the user.
- Automated remediation success/failure evaluation — not applicable, since V1 never
  executes remediation (see docs/security.md).
