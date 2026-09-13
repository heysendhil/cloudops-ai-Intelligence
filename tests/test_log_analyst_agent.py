import json
from pathlib import Path

import pytest
from crewai import LLM

from app.agents.log_analyst import (
    LOG_ANALYST_BACKSTORY,
    LOG_ANALYST_GOAL,
    LOG_ANALYST_ROLE,
    build_log_analyst_agent,
)
from app.llm_config import MissingAPIKeyError
from app.tasks.log_analysis_task import (
    DEFAULT_END_TIME,
    DEFAULT_START_TIME,
    LogAnalysisReport,
    build_log_analysis_task,
)
from app.tools.log_analysis_tool import LogAnalysisTool

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_REPORT_FIELDS = {
    "errors",
    "warnings",
    "recurring_patterns",
    "timestamps",
    "evidence",
    "summary",
    "confidence",
}


@pytest.fixture()
def fake_llm() -> LLM:
    # Construction never makes a network call, so this is safe without a real key.
    return LLM(model="gemini/gemini-2.0-flash-001", api_key="fake-test-key")


# --- Agent -----------------------------------------------------------------


def test_agent_role_goal_backstory_match_spec(fake_llm: LLM) -> None:
    agent = build_log_analyst_agent(llm=fake_llm)

    assert agent.role == "Log Analyst" == LOG_ANALYST_ROLE
    assert (
        agent.goal
        == "Analyze application logs and identify evidence relevant to the incident."
        == LOG_ANALYST_GOAL
    )
    assert agent.backstory == LOG_ANALYST_BACKSTORY


def test_agent_backstory_states_grounding_constraint() -> None:
    text = LOG_ANALYST_BACKSTORY.lower()

    assert "never speculate" in text or "never" in text
    assert "invent" in text or "fabricat" in text


def test_agent_uses_log_analysis_tool(fake_llm: LLM) -> None:
    agent = build_log_analyst_agent(llm=fake_llm)

    assert len(agent.tools) == 1
    assert isinstance(agent.tools[0], LogAnalysisTool)


def test_agent_does_not_delegate(fake_llm: LLM) -> None:
    agent = build_log_analyst_agent(llm=fake_llm)

    assert agent.allow_delegation is False


def test_build_agent_without_llm_requires_google_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError):
        build_log_analyst_agent()


# --- Task --------------------------------------------------------------


def test_task_is_assigned_to_the_given_agent(fake_llm: LLM) -> None:
    agent = build_log_analyst_agent(llm=fake_llm)

    task = build_log_analysis_task(agent)

    assert task.agent is agent


def test_task_uses_log_analysis_tool(fake_llm: LLM) -> None:
    agent = build_log_analyst_agent(llm=fake_llm)

    task = build_log_analysis_task(agent)

    assert len(task.tools) == 1
    assert isinstance(task.tools[0], LogAnalysisTool)


def test_task_expected_output_names_every_required_field(fake_llm: LLM) -> None:
    agent = build_log_analyst_agent(llm=fake_llm)
    task = build_log_analysis_task(agent)

    for field_name in REQUIRED_REPORT_FIELDS:
        assert field_name in task.expected_output


def test_task_output_pydantic_schema_has_exactly_required_fields() -> None:
    assert set(LogAnalysisReport.model_fields.keys()) == REQUIRED_REPORT_FIELDS


def test_task_output_pydantic_is_set(fake_llm: LLM) -> None:
    agent = build_log_analyst_agent(llm=fake_llm)
    task = build_log_analysis_task(agent)

    assert task.output_pydantic is LogAnalysisReport


def test_task_description_references_tool_and_forbids_invention(fake_llm: LLM) -> None:
    agent = build_log_analyst_agent(llm=fake_llm)
    task = build_log_analysis_task(agent)

    assert "log_analysis_tool" in task.description
    assert "not invent" in task.description


def test_task_description_includes_incident_and_window(fake_llm: LLM) -> None:
    agent = build_log_analyst_agent(llm=fake_llm)

    task = build_log_analysis_task(
        agent,
        incident_id="INC-TEST-0001",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-01T01:00:00Z",
    )

    assert "INC-TEST-0001" in task.description
    assert "2026-01-01T00:00:00Z" in task.description
    assert "2026-01-01T01:00:00Z" in task.description


def test_default_task_window_matches_incident_record() -> None:
    incident = json.loads((REPO_ROOT / "data" / "incidents" / "INC-2026-0912.json").read_text())

    assert DEFAULT_START_TIME == incident["time_window"]["start"]
    assert DEFAULT_END_TIME == incident["time_window"]["end"]
