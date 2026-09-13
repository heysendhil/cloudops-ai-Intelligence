import pytest
from crewai import LLM

from app.agents.incident_reporter import (
    INCIDENT_REPORTER_BACKSTORY,
    INCIDENT_REPORTER_GOAL,
    INCIDENT_REPORTER_ROLE,
    build_incident_reporter_agent,
)
from app.llm_config import MissingAPIKeyError
from app.tasks.incident_reporting_task import (
    DEFAULT_IMPACT,
    DEFAULT_SERVICE,
    DEFAULT_SEVERITY,
    IncidentReport,
    build_incident_reporting_task,
)
from _fixtures_root_cause import (
    build_fixture_cloud_report,
    build_fixture_k8s_report,
    build_fixture_knowledge_report,
    build_fixture_log_report,
    build_fixture_rca_report,
    build_fixture_remediation_report,
)

REQUIRED_REPORT_FIELDS = {
    "incident_id",
    "severity",
    "service",
    "impact",
    "timeline",
    "log_findings",
    "cloud_findings",
    "kubernetes_findings",
    "relevant_runbook",
    "root_cause",
    "alternative_hypotheses",
    "confidence",
    "remediation_recommendations",
    "human_approval_requirement",
}


@pytest.fixture()
def fake_llm() -> LLM:
    # Construction never makes a network call, so this is safe without a real key.
    return LLM(model="gemini/gemini-2.0-flash-001", api_key="fake-test-key")


@pytest.fixture()
def inputs():
    return {
        "log_analysis": build_fixture_log_report(),
        "cloud_analysis": build_fixture_cloud_report(),
        "kubernetes_analysis": build_fixture_k8s_report(),
        "knowledge_retrieval": build_fixture_knowledge_report(),
        "rca": build_fixture_rca_report(),
        "remediation": build_fixture_remediation_report(),
    }


# --- Agent -----------------------------------------------------------------


def test_agent_role_goal_backstory_match_spec(fake_llm: LLM) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)

    assert agent.role == "Incident Reporter" == INCIDENT_REPORTER_ROLE
    assert agent.goal == INCIDENT_REPORTER_GOAL
    assert agent.backstory == INCIDENT_REPORTER_BACKSTORY


def test_agent_backstory_forbids_inventing_evidence() -> None:
    text = INCIDENT_REPORTER_BACKSTORY.lower()

    assert "you compile -- you do not investigate" in text
    assert "never invent evidence" in text


def test_agent_has_no_tools(fake_llm: LLM) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)

    assert agent.tools == []


def test_agent_does_not_delegate(fake_llm: LLM) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)

    assert agent.allow_delegation is False


def test_build_agent_without_llm_requires_google_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError):
        build_incident_reporter_agent()


# --- Output structure ----------------------------------------------------


def test_report_schema_has_exactly_the_fourteen_requested_fields() -> None:
    assert set(IncidentReport.model_fields.keys()) == REQUIRED_REPORT_FIELDS
    assert len(REQUIRED_REPORT_FIELDS) == 14


def test_timeline_entry_schema_supports_source_attribution() -> None:
    from app.tasks.incident_reporting_task import TimelineEntry

    assert set(TimelineEntry.model_fields.keys()) == {"timestamp", "description", "source"}


def test_remediation_recommendations_reuse_the_exact_recommendation_schema() -> None:
    from app.tasks.remediation_recommendation_task import Recommendation

    field_info = IncidentReport.model_fields["remediation_recommendations"]
    # list[Recommendation] -- confirm it's the same type object Phase 14 defined,
    # not a redefinition that could silently drop the requires_human_approval guarantee.
    assert field_info.annotation.__args__[0] is Recommendation


def test_default_incident_metadata_matches_the_real_incident_record() -> None:
    import json
    from pathlib import Path

    incident = json.loads(
        (Path(__file__).resolve().parents[1] / "data" / "incidents" / "INC-2026-0912.json").read_text()
    )

    assert DEFAULT_SEVERITY == incident["severity"]
    assert DEFAULT_SERVICE == incident["service"]["name"]
    assert DEFAULT_IMPACT == incident["impact"]["description"]


# --- Task --------------------------------------------------------------


def test_task_is_assigned_to_the_given_agent(fake_llm: LLM, inputs: dict) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)

    task = build_incident_reporting_task(agent, **inputs)

    assert task.agent is agent


def test_task_has_no_tools(fake_llm: LLM, inputs: dict) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)

    task = build_incident_reporting_task(agent, **inputs)

    assert task.tools in (None, [])


def test_task_output_pydantic_is_set(fake_llm: LLM, inputs: dict) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)
    task = build_incident_reporting_task(agent, **inputs)

    assert task.output_pydantic is IncidentReport


def test_task_expected_output_names_every_required_field(fake_llm: LLM, inputs: dict) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)
    task = build_incident_reporting_task(agent, **inputs)

    for field_name in REQUIRED_REPORT_FIELDS:
        assert field_name in task.expected_output


def test_task_description_embeds_incident_metadata(fake_llm: LLM, inputs: dict) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)

    task = build_incident_reporting_task(
        agent,
        **inputs,
        incident_id="INC-TEST-0007",
        severity="SEV-1",
        service="Test Service",
        impact="Total outage.",
    )

    assert "INC-TEST-0007" in task.description
    assert "SEV-1" in task.description
    assert "Test Service" in task.description
    assert "Total outage." in task.description


def test_task_description_embeds_all_six_upstream_reports_verbatim(
    fake_llm: LLM, inputs: dict
) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)
    task = build_incident_reporting_task(agent, **inputs)

    assert inputs["log_analysis"].model_dump_json(indent=2) in task.description
    assert inputs["cloud_analysis"].model_dump_json(indent=2) in task.description
    assert inputs["kubernetes_analysis"].model_dump_json(indent=2) in task.description
    assert inputs["knowledge_retrieval"].model_dump_json(indent=2) in task.description
    assert inputs["rca"].model_dump_json(indent=2) in task.description
    assert inputs["remediation"].model_dump_json(indent=2) in task.description


def test_task_description_forbids_inventing_evidence(fake_llm: LLM, inputs: dict) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)
    task = build_incident_reporting_task(agent, **inputs)

    text = task.description.lower()
    assert "must not invent" in text or "do not invent" in text
    assert "only use" in text or "only information supplied" in text or "strictly" in text


def test_task_description_forbids_altering_remediation_recommendations(
    fake_llm: LLM, inputs: dict
) -> None:
    agent = build_incident_reporter_agent(llm=fake_llm)
    task = build_incident_reporting_task(agent, **inputs)

    text = task.description.lower()
    assert "do not alter, add, or drop" in text
