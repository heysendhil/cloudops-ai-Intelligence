# Runbook: Database Connection Pool Exhaustion

## Overview

This runbook covers diagnosis and recommended response for services that use a
bounded database connection pool (e.g. HikariCP, PgBouncer, SQLAlchemy pool) and
begin exhausting that pool under production load. Pool exhaustion is one of the
most common causes of cascading latency and error-rate incidents in services
backed by a relational database, because a saturated pool affects every request
path that touches the database at once, including health checks.

Applies to: any Kubernetes-deployed service with a fixed-size database connection
pool and an HTTP health/liveness endpoint that checks database connectivity.

## Symptoms

A database connection pool exhaustion incident typically presents as some or all
of the following, usually in this order:

1. Average and p95 request latency rises, often into the multi-second range, as
   requests queue waiting for a pooled connection to free up.
2. Connection pool utilization (active / max) climbs toward 100% and stays
   pegged there.
3. A growing number of threads/requests are shown as "waiting" for a connection.
4. HTTP 5xx errors increase, driven by connection-acquisition timeout exceptions
   once queued requests exceed the pool's configured `connectionTimeout`.
5. If the service's health/liveness endpoint itself depends on acquiring a
   database connection (a common default, e.g. Spring Boot Actuator's database
   health indicator), the health check starts failing under the same pressure.
6. Kubernetes liveness probe failures follow, and kubelet restarts the affected
   pods once `failureThreshold` consecutive failures are reached. Restarts do
   not fix the underlying pressure and can transiently reduce available
   capacity, prolonging the incident.

## Likely Causes

- **Long-running or newly slow queries** holding connections far longer than
  usual — e.g. a missing index, a query plan regression after a schema change,
  or a batch/reconciliation job running concurrently with normal traffic and
  competing for the same connection pool and database resources.
- **Traffic spike** exceeding the capacity the pool was sized for.
- **Connection leaks** — code paths that acquire a connection and fail to
  release it (missing `close()`/try-with-resources, exceptions bypassing
  cleanup).
- **Downstream database degradation** — elevated latency or lock contention on
  the database side (e.g. autovacuum, replication lag, another workload on a
  shared instance) that is not directly visible from the application.
- **Pool undersized for current load** relative to request concurrency and
  typical query duration.

## Diagnosis Steps

1. **Confirm pool saturation.** Check the pool's active/idle/waiting metrics
   (per-pod and aggregated). Utilization consistently at or near 100% with a
   non-zero and growing "waiting" count confirms exhaustion rather than a
   transient blip.
2. **Correlate with query duration.** Look for a rise in average query duration
   immediately preceding the utilization climb. A sudden jump points to a
   specific slow query pattern or a concurrent batch/background job; a gradual
   rise across many query types points more toward a traffic increase.
3. **Check for concurrent batch jobs.** Look for scheduled jobs (cron jobs,
   reconciliation jobs, reporting jobs) with a run window overlapping the start
   of the incident. A batch job scanning large tables is a frequent trigger.
4. **Check for a recent deployment.** Compare the incident start time against
   the most recent rollout of the service and any database schema migrations.
   If there was no recent deploy, rule out a code regression as the trigger and
   focus on query patterns, data volume, or concurrent load instead.
5. **Inspect connection-timeout errors.** Application logs should show
   connection-acquisition timeout exceptions (e.g. HikariCP's
   `SQLTransientConnectionException: ... Connection is not available, request
   timed out after <connectionTimeout>ms`) at the same time 5xx errors begin.
6. **Check pod restart timing against health-check failures.** Liveness probe
   failures that immediately precede each restart, with a "DOWN" database health
   component, confirm the health check is failing due to pool pressure rather
   than an unrelated application crash.
7. **Rule out compute exhaustion.** If CPU and memory utilization remain well
   below their limits while the pool is saturated, this points at the database
   layer (connections/queries) as the bottleneck rather than the pods being
   under-provisioned.

## Mitigation

These are read-only, advisory recommendations for a human responder to
evaluate and apply — nothing in this runbook should be treated as an automatic
action.

- **Short-term relief:** if a specific batch/background job correlates with the
  onset, pausing or deferring it can relieve pressure quickly.
- **Increase pool size cautiously**, only if the database itself has headroom
  for more concurrent connections (check the database's own max-connections
  limit and current utilization first) — a larger pool against an
  already-saturated database will not help and can make things worse.
- **Add or fix an index** if diagnosis points to a specific slow query pattern
  caused by a missing or ineffective index.
- **Move batch/reporting workloads off the primary transactional path**, e.g.
  to a read replica or an off-peak schedule, if they regularly contend with
  interactive traffic.
- **Adjust health check configuration** so liveness probes do not depend on a
  full database round-trip (or use a separate, lighter-weight liveness check
  distinct from a deeper readiness/db check), to avoid restart storms
  amplifying an already-degraded service.
- **Investigate and fix connection leaks** if pool exhaustion recurs without a
  corresponding traffic or query-duration increase.

## Prevention

- Alert on connection pool utilization and "waiting" count, not just on error
  rate or latency, so pool pressure is visible before it causes request
  failures.
- Track query duration percentiles per endpoint/query and alert on regressions.
- Schedule batch/reconciliation jobs against a read replica where possible, or
  stagger them away from peak traffic windows.
- Separate liveness checks (process is alive) from readiness/deep-health checks
  (dependencies are reachable) so a slow dependency does not directly trigger
  pod restarts.
- Load-test with realistic concurrent batch-job scenarios, not just steady-state
  traffic, when sizing the connection pool.

## References

- Related incident: INC-2026-0912 (Payment API, production, SEV-2)
