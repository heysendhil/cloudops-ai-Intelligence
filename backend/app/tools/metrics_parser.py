"""Pure-Python cloud metrics extraction core for the Cloud Metrics Tool.

No CrewAI, no LLM: this module only reads data/metrics/payment-api.json and
extracts the fields that are actually present in it. A metric that does not
exist in the source file (e.g. database memory, database query latency) is
reported as unavailable rather than estimated or fabricated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_METRICS_PATH = REPO_ROOT / "data" / "metrics" / "payment-api.json"


@dataclass(frozen=True)
class MetricPoint:
    timestamp: str
    value: float

    def to_dict(self) -> dict:
        return {"timestamp": self.timestamp, "value": self.value}


@dataclass(frozen=True)
class MetricSeries:
    """A metric extracted across all datapoints, or a documented absence.

    `available=False` (empty `points`, `source_field=None`) means the source
    file simply does not contain this metric -- it is never filled in with a
    guessed or estimated value.
    """

    metric: str
    unit: str
    available: bool
    points: list[MetricPoint] = field(default_factory=list)
    source_field: str | None = None
    reason_unavailable: str | None = None

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "unit": self.unit,
            "available": self.available,
            "points": [p.to_dict() for p in self.points],
            "source_field": self.source_field,
            "reason_unavailable": self.reason_unavailable,
        }


@dataclass(frozen=True)
class ScalarMetric:
    """A single configuration-style value (e.g. a connection limit) rather
    than a time series."""

    metric: str
    unit: str
    available: bool
    value: float | int | None
    source_field: str | None = None
    reason_unavailable: str | None = None

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "unit": self.unit,
            "available": self.available,
            "value": self.value,
            "source_field": self.source_field,
            "reason_unavailable": self.reason_unavailable,
        }


@dataclass(frozen=True)
class CloudMetricsResult:
    source_file: str
    service: str
    window: dict
    database_cpu: MetricSeries
    database_memory: MetricSeries
    database_connections: MetricSeries
    connection_limit: ScalarMetric
    active_connections: MetricSeries
    query_latency: MetricSeries
    application_cpu: MetricSeries
    application_memory: MetricSeries
    request_latency: MetricSeries
    http_5xx_percentage: MetricSeries

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "service": self.service,
            "window": self.window,
            "database_cpu": self.database_cpu.to_dict(),
            "database_memory": self.database_memory.to_dict(),
            "database_connections": self.database_connections.to_dict(),
            "connection_limit": self.connection_limit.to_dict(),
            "active_connections": self.active_connections.to_dict(),
            "query_latency": self.query_latency.to_dict(),
            "application_cpu": self.application_cpu.to_dict(),
            "application_memory": self.application_memory.to_dict(),
            "request_latency": self.request_latency.to_dict(),
            "http_5xx_percentage": self.http_5xx_percentage.to_dict(),
        }


def _series_from_field(
    datapoints: list[dict], field_name: str, metric_name: str, unit: str
) -> MetricSeries:
    if not datapoints or field_name not in datapoints[0]:
        return MetricSeries(
            metric=metric_name,
            unit=unit,
            available=False,
            reason_unavailable=f"'{field_name}' is not present in the metrics datapoints.",
        )

    points = [
        MetricPoint(timestamp=dp["timestamp"], value=dp[field_name])
        for dp in datapoints
        if field_name in dp
    ]
    return MetricSeries(
        metric=metric_name, unit=unit, available=True, points=points, source_field=field_name
    )


def _http_5xx_percentage_series(datapoints: list[dict]) -> MetricSeries:
    metric_name = "http_5xx_percentage"
    required_fields = ("http_5xx_count", "request_count")

    if not datapoints or not all(f in datapoints[0] for f in required_fields):
        return MetricSeries(
            metric=metric_name,
            unit="percent",
            available=False,
            reason_unavailable=(
                "'http_5xx_count' and/or 'request_count' are not present in the "
                "metrics datapoints, so the 5xx percentage cannot be computed."
            ),
        )

    points = [
        MetricPoint(
            timestamp=dp["timestamp"],
            value=round(dp["http_5xx_count"] / dp["request_count"] * 100, 2),
        )
        for dp in datapoints
        if all(f in dp for f in required_fields) and dp["request_count"]
    ]
    return MetricSeries(
        metric=metric_name,
        unit="percent",
        available=True,
        points=points,
        source_field="http_5xx_count / request_count",
    )


def _connection_limit(data: dict) -> ScalarMetric:
    db_pool = data.get("db_pool", {})
    if "cluster_max_size" not in db_pool:
        return ScalarMetric(
            metric="connection_limit",
            unit="connections",
            available=False,
            value=None,
            reason_unavailable="'db_pool.cluster_max_size' is not present in the metrics file.",
        )

    return ScalarMetric(
        metric="connection_limit",
        unit="connections",
        available=True,
        value=db_pool["cluster_max_size"],
        source_field="db_pool.cluster_max_size",
    )


def extract_cloud_metrics(metrics_path: Path | str = DEFAULT_METRICS_PATH) -> CloudMetricsResult:
    """Read and extract the standard cloud/infra metric set from a metrics
    JSON file. Raises FileNotFoundError if the file does not exist. Any
    requested metric not present in the source data is returned as
    unavailable rather than invented.
    """
    path = Path(metrics_path)
    if not path.is_file():
        raise FileNotFoundError(f"Metrics file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    datapoints = data.get("datapoints", [])

    return CloudMetricsResult(
        source_file=str(path),
        service=data.get("service", ""),
        window=data.get("window", {}),
        database_cpu=_series_from_field(
            datapoints, "db_cpu_utilization_pct", "database_cpu", "percent"
        ),
        database_memory=_series_from_field(
            datapoints, "db_memory_utilization_pct", "database_memory", "percent"
        ),
        database_connections=_series_from_field(
            datapoints, "db_pool_utilization_pct", "database_connections", "percent"
        ),
        connection_limit=_connection_limit(data),
        active_connections=_series_from_field(
            datapoints, "db_pool_active", "active_connections", "connections"
        ),
        query_latency=_series_from_field(
            datapoints, "db_query_latency_ms", "query_latency", "ms"
        ),
        application_cpu=_series_from_field(
            datapoints, "cpu_utilization_pct", "application_cpu", "percent"
        ),
        application_memory=_series_from_field(
            datapoints, "memory_utilization_pct", "application_memory", "percent"
        ),
        request_latency=_series_from_field(
            datapoints, "latency_ms_avg", "request_latency", "ms"
        ),
        http_5xx_percentage=_http_5xx_percentage_series(datapoints),
    )
