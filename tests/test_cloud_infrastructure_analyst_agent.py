import pytest
from crewai import LLM

from app.agents.cloud_infrastructure_analyst import (
    CLOUD_INFRA_ANALYST_BACKSTORY,
    CLOUD_INFRA_ANALYST_GOAL,
    CLOUD_INFRA_ANALYST_ROLE,
    build_cloud_infrastructure_analyst_agent,
)
from app.llm_config import MissingAPIKeyError
from app.tasks.cloud_infrastructure_analysis_task import (
    CloudInfrastructureAnalysisReport,
    build_cloud_infrastructure_analysis_task,
)
from app.tools.cloud_metrics_tool import CloudMetricsTool

REQUIRED_REPORT_FIELDS = {
    "observed_facts",
    "interpretation",
    "possible_causes",
    "summary",
    "confidence",
}


@pytest.fixture()
def fake_llm() -> LLM:
    # Construction never makes a network call, so this is safe without a real key.
    return LLM(model="gemini/gemini-2.0-flash-001", api_key="fake-test-key")


# --- Agent -----------------------------------------------------------------


def test_agent_role_goal_backstory_match_spec(fake_llm: LLM) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)

    assert agent.role == "Cloud Infrastructure Analyst" == CLOUD_INFRA_ANALYST_ROLE
    assert (
        agent.goal
        == "Identify abnormal infrastructure metrics and explain their relationship to the incident."
        == CLOUD_INFRA_ANALYST_GOAL
    )
    assert agent.backstory == CLOUD_INFRA_ANALYST_BACKSTORY


def test_agent_backstory_states_grounding_and_distinction_constraints() -> None:
    text = CLOUD_INFRA_ANALYST_BACKSTORY.lower()

    assert "invent" in text
    assert "observed facts" in text
    assert "interpretation" in text
    assert "possible causes" in text


def test_agent_uses_cloud_metrics_tool(fake_llm: LLM) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)

    assert len(agent.tools) == 1
    assert isinstance(agent.tools[0], CloudMetricsTool)


def test_agent_does_not_delegate(fake_llm: LLM) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)

    assert agent.allow_delegation is False


def test_build_agent_without_llm_requires_google_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError):
        build_cloud_infrastructure_analyst_agent()


# --- Task --------------------------------------------------------------


def test_task_is_assigned_to_the_given_agent(fake_llm: LLM) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)

    task = build_cloud_infrastructure_analysis_task(agent)

    assert task.agent is agent


def test_task_uses_cloud_metrics_tool(fake_llm: LLM) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)

    task = build_cloud_infrastructure_analysis_task(agent)

    assert len(task.tools) == 1
    assert isinstance(task.tools[0], CloudMetricsTool)


def test_task_expected_output_names_every_required_field(fake_llm: LLM) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)
    task = build_cloud_infrastructure_analysis_task(agent)

    for field_name in REQUIRED_REPORT_FIELDS:
        assert field_name in task.expected_output


def test_task_output_pydantic_schema_has_exactly_required_fields() -> None:
    assert set(CloudInfrastructureAnalysisReport.model_fields.keys()) == REQUIRED_REPORT_FIELDS


def test_observed_fact_schema_supports_traceability_and_relationship() -> None:
    from app.tasks.cloud_infrastructure_analysis_task import ObservedMetricFact

    fields = set(ObservedMetricFact.model_fields.keys())
    assert {"metric", "value", "unit", "timestamp", "source_field", "relationship_to_incident"}.issubset(
        fields
    )


def test_task_output_pydantic_is_set(fake_llm: LLM) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)
    task = build_cloud_infrastructure_analysis_task(agent)

    assert task.output_pydantic is CloudInfrastructureAnalysisReport


def test_task_description_references_tool_and_forbids_invention(fake_llm: LLM) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)
    task = build_cloud_infrastructure_analysis_task(agent)

    assert "cloud_metrics_tool" in task.description
    assert "not invent" in task.description


def test_task_description_requires_observed_interpretation_cause_distinction(
    fake_llm: LLM,
) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)
    task = build_cloud_infrastructure_analysis_task(agent)

    assert "observed facts" in task.description
    assert "interpretation" in task.description
    assert "possible causes" in task.description


def test_task_description_includes_incident_id(fake_llm: LLM) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)

    task = build_cloud_infrastructure_analysis_task(agent, incident_id="INC-TEST-0002")

    assert "INC-TEST-0002" in task.description


def test_task_description_references_custom_metrics_path(fake_llm: LLM) -> None:
    agent = build_cloud_infrastructure_analyst_agent(llm=fake_llm)

    task = build_cloud_infrastructure_analysis_task(agent, metrics_path="/tmp/custom.json")

    assert "/tmp/custom.json" in task.description
