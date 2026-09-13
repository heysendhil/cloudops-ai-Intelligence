import pytest
from crewai import LLM

from app.agents.root_cause_investigator import (
    ROOT_CAUSE_INVESTIGATOR_BACKSTORY,
    ROOT_CAUSE_INVESTIGATOR_GOAL,
    ROOT_CAUSE_INVESTIGATOR_ROLE,
    build_root_cause_investigator_agent,
)
from app.llm_config import MissingAPIKeyError
from app.tasks.root_cause_investigation_task import (
    RootCauseInvestigationReport,
    build_root_cause_investigation_task,
)
from _fixtures_root_cause import (
    build_fixture_cloud_report,
    build_fixture_k8s_report,
    build_fixture_knowledge_report,
    build_fixture_log_report,
)

REQUIRED_REPORT_FIELDS = {
    "root_cause",
    "evidence",
    "alternative_hypotheses",
    "confidence",
    "missing_evidence",
}


@pytest.fixture()
def fake_llm() -> LLM:
    # Construction never makes a network call, so this is safe without a real key.
    return LLM(model="gemini/gemini-2.0-flash-001", api_key="fake-test-key")


@pytest.fixture()
def upstream_reports():
    return {
        "log_analysis": build_fixture_log_report(),
        "cloud_analysis": build_fixture_cloud_report(),
        "kubernetes_analysis": build_fixture_k8s_report(),
        "knowledge_retrieval": build_fixture_knowledge_report(),
    }


# --- Agent -----------------------------------------------------------------


def test_agent_role_goal_backstory_match_spec(fake_llm: LLM) -> None:
    agent = build_root_cause_investigator_agent(llm=fake_llm)

    assert agent.role == "Root Cause Investigator" == ROOT_CAUSE_INVESTIGATOR_ROLE
    assert agent.goal == ROOT_CAUSE_INVESTIGATOR_GOAL
    assert agent.backstory == ROOT_CAUSE_INVESTIGATOR_BACKSTORY


def test_agent_goal_names_all_four_upstream_agents() -> None:
    text = ROOT_CAUSE_INVESTIGATOR_GOAL.lower()

    assert "log analyst" in text
    assert "cloud infrastructure analyst" in text
    assert "kubernetes reliability analyst" in text
    assert "knowledge/rag agent" in text


def test_agent_backstory_covers_all_seven_requirements() -> None:
    text = ROOT_CAUSE_INVESTIGATOR_BACKSTORY.lower()

    assert "never invent" in text  # no invented metrics
    assert "symptom" in text and "root cause" in text  # symptom vs root cause
    assert "alternative" in text  # alternative hypotheses
    assert "stronger" in text  # why leading is stronger
    assert "missing" in text  # missing evidence
    assert "confidence" in text and "calibrated" in text  # calibrated confidence


def test_agent_has_no_tools(fake_llm: LLM) -> None:
    agent = build_root_cause_investigator_agent(llm=fake_llm)

    assert agent.tools == []


def test_agent_does_not_delegate(fake_llm: LLM) -> None:
    agent = build_root_cause_investigator_agent(llm=fake_llm)

    assert agent.allow_delegation is False


def test_build_agent_without_llm_requires_google_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError):
        build_root_cause_investigator_agent()


# --- Task --------------------------------------------------------------


def test_task_is_assigned_to_the_given_agent(fake_llm: LLM, upstream_reports: dict) -> None:
    agent = build_root_cause_investigator_agent(llm=fake_llm)

    task = build_root_cause_investigation_task(agent, **upstream_reports)

    assert task.agent is agent


def test_task_has_no_tools(fake_llm: LLM, upstream_reports: dict) -> None:
    agent = build_root_cause_investigator_agent(llm=fake_llm)

    task = build_root_cause_investigation_task(agent, **upstream_reports)

    assert task.tools in (None, [])


def test_task_expected_output_names_every_required_field(
    fake_llm: LLM, upstream_reports: dict
) -> None:
    agent = build_root_cause_investigator_agent(llm=fake_llm)
    task = build_root_cause_investigation_task(agent, **upstream_reports)

    for field_name in REQUIRED_REPORT_FIELDS:
        assert field_name in task.expected_output


def test_task_output_pydantic_schema_matches_exact_requested_shape() -> None:
    assert set(RootCauseInvestigationReport.model_fields.keys()) == REQUIRED_REPORT_FIELDS


def test_task_output_pydantic_is_set(fake_llm: LLM, upstream_reports: dict) -> None:
    agent = build_root_cause_investigator_agent(llm=fake_llm)
    task = build_root_cause_investigation_task(agent, **upstream_reports)

    assert task.output_pydantic is RootCauseInvestigationReport


def test_task_description_embeds_all_four_upstream_reports_verbatim(
    fake_llm: LLM, upstream_reports: dict
) -> None:
    agent = build_root_cause_investigator_agent(llm=fake_llm)
    task = build_root_cause_investigation_task(agent, **upstream_reports)

    assert upstream_reports["log_analysis"].model_dump_json(indent=2) in task.description
    assert upstream_reports["cloud_analysis"].model_dump_json(indent=2) in task.description
    assert upstream_reports["kubernetes_analysis"].model_dump_json(indent=2) in task.description
    assert upstream_reports["knowledge_retrieval"].model_dump_json(indent=2) in task.description


def test_task_description_lists_all_seven_requirements(
    fake_llm: LLM, upstream_reports: dict
) -> None:
    agent = build_root_cause_investigator_agent(llm=fake_llm)
    task = build_root_cause_investigation_task(agent, **upstream_reports)

    text = task.description.lower()
    assert "evidence-based reasoning" in text
    assert "no invented metrics" in text
    assert "identify alternative hypotheses" in text
    assert "explain why the leading hypothesis is stronger" in text
    assert "explicitly identify missing evidence" in text
    assert "calibrate confidence" in text
    assert "do not confuse symptoms with root cause" in text


def test_task_description_includes_incident_id(fake_llm: LLM, upstream_reports: dict) -> None:
    agent = build_root_cause_investigator_agent(llm=fake_llm)

    task = build_root_cause_investigation_task(
        agent, **upstream_reports, incident_id="INC-TEST-0005"
    )

    assert "INC-TEST-0005" in task.description
