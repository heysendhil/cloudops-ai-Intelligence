"""Crew-level structural tests for the CloudOps Investigation Crew. All
offline (a fake LLM is shared across all 7 agents) -- these verify the
crew's composition and wiring, not live model behavior; see
tests/evaluation/test_cloudops_investigation_crew_evaluation.py for that.
"""

import pytest
from crewai import LLM, Process

from app.agents.cloud_infrastructure_analyst import CLOUD_INFRA_ANALYST_ROLE
from app.agents.incident_reporter import INCIDENT_REPORTER_ROLE
from app.agents.knowledge_rag import KNOWLEDGE_RAG_ROLE
from app.agents.kubernetes_reliability_analyst import KUBERNETES_ANALYST_ROLE
from app.agents.log_analyst import LOG_ANALYST_ROLE
from app.agents.remediation_advisor import REMEDIATION_ADVISOR_ROLE
from app.agents.root_cause_investigator import ROOT_CAUSE_INVESTIGATOR_ROLE
from app.crew import CREW_NAME, build_cloudops_investigation_crew

EXPECTED_ROLES_IN_ORDER = [
    LOG_ANALYST_ROLE,
    CLOUD_INFRA_ANALYST_ROLE,
    KUBERNETES_ANALYST_ROLE,
    KNOWLEDGE_RAG_ROLE,
    ROOT_CAUSE_INVESTIGATOR_ROLE,
    REMEDIATION_ADVISOR_ROLE,
    INCIDENT_REPORTER_ROLE,
]

EXPECTED_TASK_NAMES_IN_ORDER = [
    "Log Analysis Task",
    "Cloud Analysis Task",
    "Kubernetes Analysis Task",
    "Knowledge Retrieval Task",
    "Root Cause Task",
    "Remediation Task",
    "Incident Report Task",
]


@pytest.fixture()
def fake_llm() -> LLM:
    # Construction never makes a network call, so this is safe without a real key.
    return LLM(model="gemini/gemini-2.0-flash-001", api_key="fake-test-key")


@pytest.fixture()
def crew(fake_llm: LLM):
    return build_cloudops_investigation_crew(llm=fake_llm)


def test_crew_name_constant() -> None:
    assert CREW_NAME == "CloudOps Investigation Crew"


def test_crew_has_all_seven_agents_in_order(crew) -> None:
    assert [agent.role for agent in crew.agents] == EXPECTED_ROLES_IN_ORDER


def test_crew_has_all_seven_tasks_in_dependency_order(crew) -> None:
    assert [task.name for task in crew.tasks] == EXPECTED_TASK_NAMES_IN_ORDER


def test_crew_uses_sequential_process(crew) -> None:
    assert crew.process == Process.sequential


def test_each_task_is_assigned_to_its_correct_agent(crew) -> None:
    tasks_by_name = {task.name: task for task in crew.tasks}
    agents_by_role = {agent.role: agent for agent in crew.agents}

    assert tasks_by_name["Log Analysis Task"].agent is agents_by_role[LOG_ANALYST_ROLE]
    assert tasks_by_name["Cloud Analysis Task"].agent is agents_by_role[CLOUD_INFRA_ANALYST_ROLE]
    assert tasks_by_name["Kubernetes Analysis Task"].agent is agents_by_role[KUBERNETES_ANALYST_ROLE]
    assert tasks_by_name["Knowledge Retrieval Task"].agent is agents_by_role[KNOWLEDGE_RAG_ROLE]
    assert tasks_by_name["Root Cause Task"].agent is agents_by_role[ROOT_CAUSE_INVESTIGATOR_ROLE]
    assert tasks_by_name["Remediation Task"].agent is agents_by_role[REMEDIATION_ADVISOR_ROLE]
    assert tasks_by_name["Incident Report Task"].agent is agents_by_role[INCIDENT_REPORTER_ROLE]


def test_the_four_leaf_tasks_have_no_context(crew) -> None:
    tasks_by_name = {task.name: task for task in crew.tasks}

    for name in (
        "Log Analysis Task",
        "Cloud Analysis Task",
        "Kubernetes Analysis Task",
        "Knowledge Retrieval Task",
    ):
        # NOT_SPECIFIED (no explicit context) rather than an empty list --
        # these tasks have tools and need no upstream task output.
        assert not isinstance(tasks_by_name[name].context, list)


def test_root_cause_task_context_is_the_four_leaf_tasks(crew) -> None:
    tasks_by_name = {task.name: task for task in crew.tasks}
    root_cause_task = tasks_by_name["Root Cause Task"]

    assert isinstance(root_cause_task.context, list)
    assert [t.name for t in root_cause_task.context] == [
        "Log Analysis Task",
        "Cloud Analysis Task",
        "Kubernetes Analysis Task",
        "Knowledge Retrieval Task",
    ]


def test_remediation_task_context_is_root_cause_and_knowledge(crew) -> None:
    tasks_by_name = {task.name: task for task in crew.tasks}
    remediation_task = tasks_by_name["Remediation Task"]

    assert isinstance(remediation_task.context, list)
    assert [t.name for t in remediation_task.context] == ["Root Cause Task", "Knowledge Retrieval Task"]


def test_incident_report_task_context_is_all_six_upstream_tasks(crew) -> None:
    tasks_by_name = {task.name: task for task in crew.tasks}
    incident_report_task = tasks_by_name["Incident Report Task"]

    assert isinstance(incident_report_task.context, list)
    assert [t.name for t in incident_report_task.context] == [
        "Log Analysis Task",
        "Cloud Analysis Task",
        "Kubernetes Analysis Task",
        "Knowledge Retrieval Task",
        "Root Cause Task",
        "Remediation Task",
    ]


def test_every_context_task_appears_earlier_in_the_crew_task_list(crew) -> None:
    # Required for Process.sequential to actually have each context task's
    # .output populated by the time the downstream task runs.
    seen: list[str] = []
    for task in crew.tasks:
        if isinstance(task.context, list):
            for context_task in task.context:
                assert context_task.name in seen, (
                    f"{task.name}'s context includes {context_task.name}, which has not "
                    "executed yet at this point in the sequential task list"
                )
        seen.append(task.name)


def test_crew_without_llm_requires_google_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    from app.llm_config import MissingAPIKeyError

    with pytest.raises(MissingAPIKeyError):
        build_cloudops_investigation_crew()


def test_crew_accepts_custom_incident_metadata(fake_llm: LLM) -> None:
    crew = build_cloudops_investigation_crew(
        incident_id="INC-TEST-0099",
        severity="SEV-1",
        service="Test Service",
        impact="Total outage.",
        llm=fake_llm,
    )

    tasks_by_name = {task.name: task for task in crew.tasks}
    assert "INC-TEST-0099" in tasks_by_name["Log Analysis Task"].description
    incident_report_description = tasks_by_name["Incident Report Task"].description
    assert "INC-TEST-0099" in incident_report_description
    assert "SEV-1" in incident_report_description
    assert "Test Service" in incident_report_description
    assert "Total outage." in incident_report_description
