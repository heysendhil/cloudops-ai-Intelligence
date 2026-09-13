"""End-to-end evaluation of the CloudOps Incident Investigation Flow against
the real INC-2026-0912 golden scenario, using the real CloudOps
Investigation Crew (not the stub used in tests/test_flow.py) -- the
complete Agent -> Task -> Crew -> Flow stack, triggered exactly as a real
caller would: `flow.kickoff(inputs={"incident_id": "INC-2026-0912"})`.

Requires a real GOOGLE_API_KEY and is skipped gracefully without one, per
the project's "handle missing API keys gracefully" rule.
"""

from __future__ import annotations

import pytest

from app.flow import CloudOpsInvestigationFlow
from app.llm_config import is_configured

pytestmark = [
    pytest.mark.live_llm,
    pytest.mark.skipif(
        not is_configured(),
        reason=(
            "GOOGLE_API_KEY is not set -- skipping the live end-to-end Flow run. Set it in "
            "backend/.env to run a complete simulated investigation against a real model."
        ),
    ),
]


@pytest.fixture(scope="module")
def result():
    flow = CloudOpsInvestigationFlow()
    return flow.kickoff(inputs={"incident_id": "INC-2026-0912"})


def test_flow_succeeds_end_to_end(result: dict) -> None:
    assert result["status"] == "succeeded"
    assert result["error"] is None


def test_flow_produces_a_complete_incident_report(result: dict) -> None:
    report = result["incident_report"]

    assert report is not None
    assert report["incident_id"] == "INC-2026-0912"
    assert report["severity"] == "SEV-2"
    assert report["service"] == "Payment API"
    assert report["root_cause"]
    assert report["remediation_recommendations"]


def test_flow_result_requires_human_approval(result: dict) -> None:
    assert result["requires_human_approval"] is True
    for rec in result["incident_report"]["remediation_recommendations"]:
        assert rec["requires_human_approval"] is True
