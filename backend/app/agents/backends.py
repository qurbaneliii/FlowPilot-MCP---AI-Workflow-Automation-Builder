import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from app.agents.errors import AgentNotConfiguredError, AgentPermanentError
from app.workflow.exceptions import PermanentError, TransientError


class AgentBackendMode(str, Enum):
    REAL = "real"
    FAKE = "fake"
    UNAVAILABLE = "unavailable"


class AgentBackendPort(ABC):
    @property
    @abstractmethod
    def mode(self) -> AgentBackendMode: ...

    @abstractmethod
    async def invoke(
        self,
        *,
        agent_name: str,
        system_prompt: str,
        input_payload: dict[str, Any],
        validation_error: str | None = None,
    ) -> dict[str, Any]: ...


class OpenAIAgentBackend(AgentBackendPort):
    def __init__(self, *, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    @property
    def mode(self) -> AgentBackendMode:
        return AgentBackendMode.REAL

    async def invoke(
        self,
        *,
        agent_name: str,
        system_prompt: str,
        input_payload: dict[str, Any],
        validation_error: str | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise AgentNotConfiguredError(agent_name, "OPENAI_API_KEY is missing")
        try:
            import agents  # noqa: F401
        except ImportError as exc:
            raise AgentNotConfiguredError(
                agent_name,
                "OpenAI Agents SDK is not installed in this environment",
            ) from exc
        raise AgentNotConfiguredError(
            agent_name,
            "OpenAI Agents SDK transport is intentionally not invoked in tests",
        )


class UnavailableAgentBackend(AgentBackendPort):
    @property
    def mode(self) -> AgentBackendMode:
        return AgentBackendMode.UNAVAILABLE

    async def invoke(
        self,
        *,
        agent_name: str,
        system_prompt: str,
        input_payload: dict[str, Any],
        validation_error: str | None = None,
    ) -> dict[str, Any]:
        raise AgentNotConfiguredError(agent_name, "agent backend mode is unavailable")


class FakeAgentBackend(AgentBackendPort):
    def __init__(
        self,
        responses: list[dict[str, Any]] | None = None,
        *,
        transient_errors_before_success: int = 0,
        permanent_error: bool = False,
        sleep_seconds: float = 0,
    ) -> None:
        self.responses = list(responses or [])
        self.transient_errors_before_success = transient_errors_before_success
        self.permanent_error = permanent_error
        self.sleep_seconds = sleep_seconds
        self.calls: list[dict[str, Any]] = []

    @property
    def mode(self) -> AgentBackendMode:
        return AgentBackendMode.FAKE

    async def invoke(
        self,
        *,
        agent_name: str,
        system_prompt: str,
        input_payload: dict[str, Any],
        validation_error: str | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "agent_name": agent_name,
                "input_payload": input_payload,
                "validation_error": validation_error,
            }
        )
        if self.sleep_seconds:
            await asyncio.sleep(self.sleep_seconds)
        if self.permanent_error:
            raise PermanentError("fake permanent agent failure")
        if self.transient_errors_before_success > 0:
            self.transient_errors_before_success -= 1
            raise TransientError("fake transient agent failure")
        if self.responses:
            return self.responses.pop(0)
        return default_fake_response(agent_name, input_payload)


def default_fake_response(
    agent_name: str, input_payload: dict[str, Any]
) -> dict[str, Any]:
    if agent_name == "planner":
        prompt = str(input_payload.get("prompt", "")).lower()
        if not any(
            token in prompt for token in ["github", "repo", "audit", "readme", "issue"]
        ):
            return {
                "nodes": [
                    {
                        "id": "manual_trigger",
                        "type": "manual_trigger",
                        "name": "Unsupported request captured",
                        "config": {
                            "unsupported_use_case": True,
                            "explanation": "FlowPilot MVP only supports GitHub repo audits.",
                        },
                        "dependencies": [],
                    }
                ]
            }
        return github_repo_audit_graph(input_payload.get("repo_url", ""))
    if agent_name == "validator":
        return {"valid": True, "issues": [], "corrected_graph": None}
    if agent_name == "repo_analyzer":
        return {
            "findings": [
                {
                    "category": "documentation",
                    "severity": "warning",
                    "title": "README should include setup instructions",
                    "description": "The README needs clearer installation and configuration guidance.",
                    "recommendation": "Add setup, environment, and usage sections.",
                    "affected_files": ["README.md"],
                    "suggested_issue_title": "Improve README setup instructions",
                }
            ],
            "risk_flags": [
                {
                    "code": "MISSING_ENV_EXAMPLE",
                    "severity": "warning",
                    "description": "The repository does not include a clear .env.example file.",
                }
            ],
            "summary": "Repository is audit-ready but needs documentation polish.",
        }
    if agent_name == "readme_reviewer":
        return {
            "quality_score": 68,
            "missing_sections": ["Environment variables", "Deployment"],
            "suggestions": ["Add setup steps", "Document configuration"],
            "improved_outline": ["Overview", "Setup", "Usage", "Deployment"],
        }
    if agent_name == "issue_generator":
        return {
            "issues": [
                {
                    "title": "Improve README setup instructions",
                    "body": "Add setup, environment, and usage instructions.",
                    "labels": ["documentation", "priority:medium"],
                    "priority": "medium",
                    "acceptance_criteria": [
                        "README includes install steps",
                        "README documents required environment variables",
                    ],
                }
            ]
        }
    if agent_name == "linkedin_draft":
        return {
            "post_text": "Draft: I built a local AI workflow engine that audits GitHub repositories and produces review artifacts.",
            "hashtags": ["#AI", "#Automation"],
            "tone": "professional",
        }
    if agent_name == "executor":
        return {"result": {"ok": True}}
    raise AgentPermanentError(agent_name, "unknown fake agent")


def github_repo_audit_graph(repo_url: str) -> dict[str, Any]:
    sequence = [
        ("manual_trigger", "manual_trigger", []),
        ("github_repo_reader", "github_repo_reader", ["manual_trigger"]),
        ("ai_repo_analyzer", "ai_repo_analyzer", ["github_repo_reader"]),
        ("readme_reviewer", "readme_reviewer", ["github_repo_reader"]),
        (
            "issue_draft_generator",
            "issue_draft_generator",
            ["ai_repo_analyzer", "readme_reviewer"],
        ),
        ("human_approval", "human_approval", ["issue_draft_generator"]),
        ("github_issue_creator", "github_issue_creator", ["human_approval"]),
        (
            "linkedin_draft_generator",
            "linkedin_draft_generator",
            ["ai_repo_analyzer", "readme_reviewer"],
        ),
        (
            "markdown_report_writer",
            "markdown_report_writer",
            ["github_issue_creator", "linkedin_draft_generator"],
        ),
    ]
    return {
        "nodes": [
            {
                "id": node_id,
                "type": node_type,
                "name": node_id.replace("_", " ").title(),
                "config": {"repo_url": repo_url} if node_id == "manual_trigger" else {},
                "dependencies": dependencies,
            }
            for node_id, node_type, dependencies in sequence
        ]
    }
