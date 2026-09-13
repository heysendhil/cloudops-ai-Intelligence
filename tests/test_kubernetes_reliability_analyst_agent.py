import pytest
from crewai import LLM

from app.agents.kubernetes_reliability_analyst import (
    KUBERNETES_ANALYST_BACKSTORY,
    KUBERNETES_ANALYST_GOAL,
    KUBERNETES_ANALYST_ROLE,
    build_kubernetes_reliability_analyst_agent,
)
from app.llm_config import MissingAPIKeyError
from app.tasks.kubernetes_reliability_analysis_task import (
    KubernetesReliabilityReport,
    build_kubernetes_reliability_analysis_task,
)
from app.tools.kubernetes_reliability_tool import KubernetesReliabilityTool

REQUIRED_REPORT_FIELDS = {
    "deployment_healthy",
    "deployment_health_explanation",
    "pod_restart_patterns",
    "probe_failures",
    "relevant_events",
    "root_cause_assessment",
    "root_cause_reasoning",
    "summary",
    "confidence",
}


@pytest.fixture()
def fake_llm() -> LLM:
    # Construction never makes a network call, so this is safe without a real key.
    return LLM(model="gemini/gemini-2.0-flash-001", api_key="fake-test-key")


# --- Agent -----------------------------------------------------------------


def test_agent_role_goal_backstory_match_spec(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)

    assert agent.role == "Kubernetes Reliability Analyst" == KUBERNETES_ANALYST_ROLE
    assert agent.goal == KUBERNETES_ANALYST_GOAL
    assert agent.backstory == KUBERNETES_ANALYST_BACKSTORY


def test_agent_goal_covers_health_and_root_cause_vs_consequence() -> None:
    text = KUBERNETES_ANALYST_GOAL.lower()

    assert "healthy" in text or "health" in text
    assert "root cause" in text
    assert "consequence" in text


def test_agent_backstory_forbids_assuming_kubernetes_is_root_cause() -> None:
    text = KUBERNETES_ANALYST_BACKSTORY.lower()

    assert "never assume kubernetes is the root cause" in text
    assert "invent" in text


def test_agent_uses_kubernetes_reliability_tool(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)

    assert len(agent.tools) == 1
    assert isinstance(agent.tools[0], KubernetesReliabilityTool)


def test_agent_does_not_delegate(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)

    assert agent.allow_delegation is False


def test_build_agent_without_llm_requires_google_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError):
        build_kubernetes_reliability_analyst_agent()


# --- Task --------------------------------------------------------------


def test_task_is_assigned_to_the_given_agent(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)

    task = build_kubernetes_reliability_analysis_task(agent)

    assert task.agent is agent


def test_task_uses_kubernetes_reliability_tool(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)

    task = build_kubernetes_reliability_analysis_task(agent)

    assert len(task.tools) == 1
    assert isinstance(task.tools[0], KubernetesReliabilityTool)


def test_task_expected_output_names_every_required_field(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)
    task = build_kubernetes_reliability_analysis_task(agent)

    for field_name in REQUIRED_REPORT_FIELDS:
        assert field_name in task.expected_output


def test_task_output_pydantic_schema_has_exactly_required_fields() -> None:
    assert set(KubernetesReliabilityReport.model_fields.keys()) == REQUIRED_REPORT_FIELDS


def test_root_cause_assessment_is_constrained_to_three_values() -> None:
    field_info = KubernetesReliabilityReport.model_fields["root_cause_assessment"]
    # typing.Literal["likely_root_cause", "likely_consequence", "inconclusive"]
    allowed_values = set(field_info.annotation.__args__)

    assert allowed_values == {"likely_root_cause", "likely_consequence", "inconclusive"}


def test_task_output_pydantic_is_set(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)
    task = build_kubernetes_reliability_analysis_task(agent)

    assert task.output_pydantic is KubernetesReliabilityReport


def test_task_description_references_tool_and_forbids_invention(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)
    task = build_kubernetes_reliability_analysis_task(agent)

    assert "kubernetes_reliability_tool" in task.description
    assert "not invent" in task.description


def test_task_description_forbids_assuming_kubernetes_is_root_cause(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)
    task = build_kubernetes_reliability_analysis_task(agent)

    assert "do not assume kubernetes is the root cause" in task.description.lower()


def test_task_description_requires_all_five_determinations(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)
    task = build_kubernetes_reliability_analysis_task(agent)

    text = task.description.lower()
    assert "healthy" in text
    assert "restart pattern" in text
    assert "probe failure" in text
    assert "event" in text
    assert "root cause" in text and "consequence" in text


def test_task_description_includes_incident_id(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)

    task = build_kubernetes_reliability_analysis_task(agent, incident_id="INC-TEST-0003")

    assert "INC-TEST-0003" in task.description


def test_task_description_references_custom_k8s_path(fake_llm: LLM) -> None:
    agent = build_kubernetes_reliability_analyst_agent(llm=fake_llm)

    task = build_kubernetes_reliability_analysis_task(agent, k8s_path="/tmp/custom-k8s.json")

    assert "/tmp/custom-k8s.json" in task.description
