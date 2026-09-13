"""CrewAI-compatible wrapper around the metrics_parser core.

This module only adapts extract_cloud_metrics to CrewAI's BaseTool contract
(name, description, args_schema, _run). All extraction logic lives in
metrics_parser.py and has no CrewAI or LLM dependency -- this tool is not
wired to any Agent, Crew, or Flow yet.
"""

from __future__ import annotations

from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app.tools.metrics_parser import DEFAULT_METRICS_PATH, extract_cloud_metrics


class CloudMetricsToolInput(BaseModel):
    metrics_path: str | None = Field(
        default=None,
        description="Path to the metrics JSON file to read. Defaults to data/metrics/payment-api.json.",
    )


class CloudMetricsTool(BaseTool):
    """Reads a cloud/application metrics JSON file and extracts database CPU,
    database memory, database connections, connection limit, active
    connections, query latency, application CPU, application memory, request
    latency, and HTTP 5xx percentage. Uses no LLM -- pure JSON field
    extraction and arithmetic on real counts. Any metric absent from the
    source file is reported as unavailable, never invented.
    """

    name: str = "cloud_metrics_tool"
    description: str = (
        "Reads a CloudOps metrics JSON file and extracts database CPU, database memory, "
        "database connections, connection limit, active connections, query latency, "
        "application CPU, application memory, request latency, and HTTP 5xx percentage. "
        "Every value is read or computed directly from the source file's fields -- a "
        "metric not present in the source data is reported as unavailable rather than "
        "invented."
    )
    args_schema: type[BaseModel] = CloudMetricsToolInput

    def _run(self, metrics_path: str | None = None) -> dict:
        result = extract_cloud_metrics(Path(metrics_path) if metrics_path else DEFAULT_METRICS_PATH)
        return result.to_dict()
