"""CloudOps Investigation Crew.

Assembles all 7 agents and their tasks (see docs/agent-design.md) into a
single sequential-process CrewAI Crew:

    Log Analyst              -> Log Analysis Task              \\
    Cloud Infrastructure     -> Cloud Analysis Task              |-- independent evidence gathering
    Kubernetes Reliability   -> Kubernetes Analysis Task         |
    Knowledge/RAG Agent      -> Knowledge Retrieval Task        /
    Root Cause Investigator  -> Root Cause Task       (context: the four above)
    Remediation Advisor      -> Remediation Task       (context: Root Cause + Knowledge)
    Incident Reporter        -> Incident Report Task   (context: all six above)

Task outputs are passed to downstream tasks via CrewAI's native `context`
mechanism (Task(context=[...])), not by pre-embedding JSON -- the Crew
engine injects each context task's output into the downstream task's
prompt automatically once it completes, since Process.sequential executes
`tasks` in list order and every task appears after everything it depends
on. No Flow is defined here (see CLAUDE.md: that's a separate, later
architectural layer).
"""

from __future__ import annotations

from crewai import LLM, Crew, Process

from app.agents.cloud_infrastructure_analyst import build_cloud_infrastructure_analyst_agent
from app.agents.incident_reporter import build_incident_reporter_agent
from app.agents.knowledge_rag import build_knowledge_rag_agent
from app.agents.kubernetes_reliability_analyst import build_kubernetes_reliability_analyst_agent
from app.agents.log_analyst import build_log_analyst_agent
from app.agents.remediation_advisor import build_remediation_advisor_agent
from app.agents.root_cause_investigator import build_root_cause_investigator_agent
from app.tasks.cloud_infrastructure_analysis_task import build_cloud_infrastructure_analysis_task
from app.tasks.incident_reporting_task import (
    DEFAULT_IMPACT,
    DEFAULT_INCIDENT_ID,
    DEFAULT_SERVICE,
    DEFAULT_SEVERITY,
    build_incident_reporting_task_from_context,
)
from app.tasks.knowledge_retrieval_task import build_knowledge_retrieval_task
from app.tasks.kubernetes_reliability_analysis_task import build_kubernetes_reliability_analysis_task
from app.tasks.log_analysis_task import build_log_analysis_task
from app.tasks.remediation_recommendation_task import build_remediation_recommendation_task_from_context
from app.tasks.root_cause_investigation_task import build_root_cause_investigation_task_from_context

CREW_NAME = "CloudOps Investigation Crew"

# The 7 task names, in pipeline order, exactly as set on each Task below.
# Single source of truth for anything that needs to know the pipeline shape
# without running it -- e.g. app/investigations.py seeds each new
# investigation job with one pending entry per name here.
CREW_TASK_NAMES = [
    "Log Analysis Task",
    "Cloud Analysis Task",
    "Kubernetes Analysis Task",
    "Knowledge Retrieval Task",
    "Root Cause Task",
    "Remediation Task",
    "Incident Report Task",
]


def build_cloudops_investigation_crew(
    incident_id: str = DEFAULT_INCIDENT_ID,
    severity: str = DEFAULT_SEVERITY,
    service: str = DEFAULT_SERVICE,
    impact: str = DEFAULT_IMPACT,
    verbose: bool = False,
    llm: LLM | None = None,
) -> Crew:
    """Build the CloudOps Investigation Crew for one incident.

    Each agent and task is freshly constructed (no shared mutable state
    across separate crew builds), wired with Process.sequential, and task
    outputs are passed to downstream tasks via CrewAI's `context`
    mechanism rather than pre-computed JSON.

    Args:
        llm: LLM client shared by all 7 agents. Defaults to the project's
            configured Gemini client (requires GOOGLE_API_KEY) if not
            provided -- pass an explicit llm (e.g. a fake, in tests) to
            build the crew without that requirement.
    """
    log_agent = build_log_analyst_agent(llm=llm)
    cloud_agent = build_cloud_infrastructure_analyst_agent(llm=llm)
    kubernetes_agent = build_kubernetes_reliability_analyst_agent(llm=llm)
    knowledge_agent = build_knowledge_rag_agent(llm=llm)
    root_cause_agent = build_root_cause_investigator_agent(llm=llm)
    remediation_agent = build_remediation_advisor_agent(llm=llm)
    reporter_agent = build_incident_reporter_agent(llm=llm)

    log_task = build_log_analysis_task(log_agent, incident_id=incident_id)
    cloud_task = build_cloud_infrastructure_analysis_task(cloud_agent, incident_id=incident_id)
    kubernetes_task = build_kubernetes_reliability_analysis_task(
        kubernetes_agent, incident_id=incident_id
    )
    knowledge_task = build_knowledge_retrieval_task(knowledge_agent, incident_id=incident_id)

    root_cause_task = build_root_cause_investigation_task_from_context(
        root_cause_agent,
        context_tasks=[log_task, cloud_task, kubernetes_task, knowledge_task],
        incident_id=incident_id,
    )
    remediation_task = build_remediation_recommendation_task_from_context(
        remediation_agent,
        context_tasks=[root_cause_task, knowledge_task],
        incident_id=incident_id,
    )
    incident_report_task = build_incident_reporting_task_from_context(
        reporter_agent,
        context_tasks=[
            log_task,
            cloud_task,
            kubernetes_task,
            knowledge_task,
            root_cause_task,
            remediation_task,
        ],
        incident_id=incident_id,
        severity=severity,
        service=service,
        impact=impact,
    )

    (
        log_task.name,
        cloud_task.name,
        kubernetes_task.name,
        knowledge_task.name,
        root_cause_task.name,
        remediation_task.name,
        incident_report_task.name,
    ) = CREW_TASK_NAMES

    return Crew(
        agents=[
            log_agent,
            cloud_agent,
            kubernetes_agent,
            knowledge_agent,
            root_cause_agent,
            remediation_agent,
            reporter_agent,
        ],
        tasks=[
            log_task,
            cloud_task,
            kubernetes_task,
            knowledge_task,
            root_cause_task,
            remediation_task,
            incident_report_task,
        ],
        process=Process.sequential,
        verbose=verbose,
    )
