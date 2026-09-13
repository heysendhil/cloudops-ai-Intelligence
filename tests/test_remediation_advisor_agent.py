import pytest
from crewai import LLM

from app.agents.remediation_advisor import (
    REMEDIATION_ADVISOR_BACKSTORY,
    REMEDIATION_ADVISOR_GOAL,
    REMEDIATION_ADVISOR_ROLE,
    build_remediation_advisor_agent,
)
from app.llm_config import MissingAPIKeyError
from app.tasks.remediation_recommendation_task import (
    Recommendation,
    RemediationRecommendationReport,
    build_remediation_recommendation_task,
)
from _fixtures_root_cause import build_fixture_knowledge_report, build_fixture_rca_report

REQUIRED_REPORT_FIELDS = {"recommendations", "safety_notice", "summary", "confidence"}
REQUIRED_RECOMMENDATION_FIELDS = {"action", "reason", "risk", "requires_human_approval"}


@pytest.fixture()
def fake_llm() -> LLM:
    # Construction never makes a network call, so this is safe without a real key.
    return LLM(model="gemini/gemini-2.0-flash-001", api_key="fake-test-key")


@pytest.fixture()
def inputs():
    return {"rca": build_fixture_rca_report(), "knowledge": build_fixture_knowledge_report()}


# --- Agent -----------------------------------------------------------------


def test_agent_role_goal_backstory_match_spec(fake_llm: LLM) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)

    assert agent.role == "Remediation Advisor" == REMEDIATION_ADVISOR_ROLE
    assert agent.goal == REMEDIATION_ADVISOR_GOAL
    assert agent.backstory == REMEDIATION_ADVISOR_BACKSTORY


def test_agent_goal_states_never_execute_and_human_approval() -> None:
    text = REMEDIATION_ADVISOR_GOAL.lower()

    assert "never executing" in text
    assert "human approval" in text


def test_agent_backstory_covers_safety_and_grounding() -> None:
    text = REMEDIATION_ADVISOR_BACKSTORY.lower()

    assert "never execute" in text
    assert "requires human approval" in text
    assert "ground" in text  # evidence grounding
    assert "never invent" in text
    assert "risk" in text  # honest risk statements


def test_agent_has_no_tools(fake_llm: LLM) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)

    assert agent.tools == []


def test_agent_does_not_delegate(fake_llm: LLM) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)

    assert agent.allow_delegation is False


def test_build_agent_without_llm_requires_google_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError):
        build_remediation_advisor_agent()


# --- Recommendation schema: the hard safety guarantee ----------------------


def test_recommendation_requires_human_approval_is_type_locked_to_true() -> None:
    Recommendation(action="a", reason="b", risk="low", requires_human_approval=True)

    with pytest.raises(Exception):
        Recommendation(action="a", reason="b", risk="low", requires_human_approval=False)


def test_recommendation_schema_has_exactly_the_required_four_fields() -> None:
    assert set(Recommendation.model_fields.keys()) == REQUIRED_RECOMMENDATION_FIELDS


# --- Task --------------------------------------------------------------


def test_task_is_assigned_to_the_given_agent(fake_llm: LLM, inputs: dict) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)

    task = build_remediation_recommendation_task(agent, **inputs)

    assert task.agent is agent


def test_task_has_no_tools(fake_llm: LLM, inputs: dict) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)

    task = build_remediation_recommendation_task(agent, **inputs)

    assert task.tools in (None, [])


def test_task_expected_output_names_every_required_field(fake_llm: LLM, inputs: dict) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)
    task = build_remediation_recommendation_task(agent, **inputs)

    for field_name in REQUIRED_REPORT_FIELDS | REQUIRED_RECOMMENDATION_FIELDS:
        assert field_name in task.expected_output


def test_task_output_pydantic_schema_matches_exact_requested_shape() -> None:
    assert set(RemediationRecommendationReport.model_fields.keys()) == REQUIRED_REPORT_FIELDS


def test_task_output_pydantic_is_set(fake_llm: LLM, inputs: dict) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)
    task = build_remediation_recommendation_task(agent, **inputs)

    assert task.output_pydantic is RemediationRecommendationReport


def test_task_description_embeds_rca_and_knowledge_verbatim(
    fake_llm: LLM, inputs: dict
) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)
    task = build_remediation_recommendation_task(agent, **inputs)

    assert inputs["rca"].model_dump_json(indent=2) in task.description
    assert inputs["knowledge"].model_dump_json(indent=2) in task.description


def test_task_description_lists_all_four_requirements(fake_llm: LLM, inputs: dict) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)
    task = build_remediation_recommendation_task(agent, **inputs)

    text = task.description.lower()
    assert "recommendation quality" in text
    assert "safety" in text and "never execute" in text
    assert "evidence grounding" in text
    assert "approval requirement" in text and "human approval" in text


def test_task_description_forbids_claiming_execution(fake_llm: LLM, inputs: dict) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)
    task = build_remediation_recommendation_task(agent, **inputs)

    text = task.description.lower()
    assert "you have no ability to act on any system" in text


def test_task_description_includes_incident_id(fake_llm: LLM, inputs: dict) -> None:
    agent = build_remediation_advisor_agent(llm=fake_llm)

    task = build_remediation_recommendation_task(agent, **inputs, incident_id="INC-TEST-0006")

    assert "INC-TEST-0006" in task.description
