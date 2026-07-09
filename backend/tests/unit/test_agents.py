from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from app.agents import (
    ExecutorAgent,
    IssueGeneratorAgent,
    LinkedInDraftAgent,
    PlannerAgent,
    ReadmeReviewerAgent,
    RepoAnalyzerAgent,
    ValidatorAgent,
)
from app.agents.backends import FakeAgentBackend, OpenAIAgentBackend
from app.agents.errors import AgentNotConfiguredError, AgentOutputValidationError
from app.agents.schemas import (
    ExecutorOutput,
    IssueGeneratorOutput,
    LinkedInDraftOutput,
    ReadmeReviewerOutput,
    RepoAnalyzerOutput,
    ValidatorOutput,
)
from app.workflow import node_registry
from app.workflow.exceptions import PermanentError
from app.workflow.graph import WorkflowGraph
from tests.fixtures.fake_node_handlers import NoOpSuccessHandler


def workflow_graph_response() -> dict[str, Any]:
    return {
        "nodes": [
            {
                "id": "manual_trigger",
                "type": "manual_trigger",
                "name": "Manual Trigger",
                "config": {"repo_url": "https://github.com/example/project"},
                "dependencies": [],
            }
        ]
    }


def safe_validator_graph() -> dict[str, Any]:
    return workflow_graph_response()


VALID_RESPONSES: dict[str, dict[str, Any]] = {
    "planner": workflow_graph_response(),
    "validator": {"valid": True, "issues": [], "corrected_graph": None},
    "repo_analyzer": {
        "findings": [
            {
                "category": "documentation",
                "severity": "warning",
                "title": "README lacks setup instructions",
                "description": "The README does not explain local setup.",
                "recommendation": "Add install, env, and run steps.",
                "affected_files": ["README.md"],
                "suggested_issue_title": "Improve README setup instructions",
            }
        ],
        "risk_flags": [
            {
                "code": "MISSING_ENV_EXAMPLE",
                "severity": "warning",
                "description": "No .env.example file was found in the snapshot.",
            }
        ],
        "summary": "The repository is usable but needs documentation polish.",
    },
    "readme_reviewer": {
        "quality_score": 72,
        "missing_sections": ["Environment variables"],
        "suggestions": ["Document local setup"],
        "improved_outline": ["Overview", "Setup", "Usage", "Deployment"],
    },
    "issue_generator": {
        "issues": [
            {
                "title": "Improve README setup instructions",
                "body": "Add installation, environment, and usage instructions.",
                "labels": ["documentation", "priority:medium"],
                "priority": "medium",
                "acceptance_criteria": ["README documents setup"],
            }
        ]
    },
    "linkedin_draft": {
        "post_text": "Draft: I built a local AI workflow automation engine for repository audits.",
        "hashtags": ["#AI", "#Automation"],
        "tone": "professional",
    },
    "executor": {"result": {"ok": True}},
}


AGENT_CASES: list[
    tuple[
        str,
        Callable[[Any], Any],
        type[BaseModel],
        dict[str, Any],
    ]
] = [
    (
        "planner",
        PlannerAgent,
        WorkflowGraph,
        {
            "prompt": "Audit this GitHub repo",
            "repo_url": "https://github.com/example/project",
        },
    ),
    ("validator", ValidatorAgent, ValidatorOutput, {"graph": safe_validator_graph()}),
    ("repo_analyzer", RepoAnalyzerAgent, RepoAnalyzerOutput, {"repo_snapshot": {}}),
    ("readme_reviewer", ReadmeReviewerAgent, ReadmeReviewerOutput, {"readme": "# App"}),
    ("issue_generator", IssueGeneratorAgent, IssueGeneratorOutput, {"findings": []}),
    ("linkedin_draft", LinkedInDraftAgent, LinkedInDraftOutput, {"artifacts": []}),
    ("executor", ExecutorAgent, ExecutorOutput, {"task": "summarize"}),
]


@pytest.mark.parametrize(
    ("agent_name", "agent_cls", "_schema", "input_payload"), AGENT_CASES
)
@pytest.mark.asyncio
async def test_agent_not_configured_without_api_key(
    agent_name: str,
    agent_cls: Callable[[Any], Any],
    _schema: type[BaseModel],
    input_payload: dict[str, Any],
) -> None:
    agent = agent_cls(OpenAIAgentBackend(api_key=None, model="gpt-test"))

    with pytest.raises(AgentNotConfiguredError) as exc_info:
        await agent.run(input_payload)

    assert agent_name in str(exc_info.value)


@pytest.mark.parametrize(
    ("agent_name", "agent_cls", "schema", "input_payload"), AGENT_CASES
)
@pytest.mark.asyncio
async def test_agent_returns_valid_output_on_first_response(
    agent_name: str,
    agent_cls: Callable[[Any], Any],
    schema: type[BaseModel],
    input_payload: dict[str, Any],
) -> None:
    backend = FakeAgentBackend(responses=[VALID_RESPONSES[agent_name]])
    result = await agent_cls(backend).run(input_payload)

    assert isinstance(result, schema)
    assert len(backend.calls) == 1


@pytest.mark.parametrize(
    ("agent_name", "agent_cls", "schema", "input_payload"), AGENT_CASES
)
@pytest.mark.asyncio
async def test_agent_reprompts_once_on_invalid_response_then_succeeds(
    agent_name: str,
    agent_cls: Callable[[Any], Any],
    schema: type[BaseModel],
    input_payload: dict[str, Any],
) -> None:
    backend = FakeAgentBackend(
        responses=[{"unexpected": "shape"}, VALID_RESPONSES[agent_name]]
    )

    result = await agent_cls(backend).run(input_payload)

    assert isinstance(result, schema)
    assert len(backend.calls) == 2
    assert backend.calls[1]["validation_error"]


@pytest.mark.parametrize(
    ("_agent_name", "agent_cls", "_schema", "input_payload"), AGENT_CASES
)
@pytest.mark.asyncio
async def test_agent_fails_after_second_invalid_response(
    _agent_name: str,
    agent_cls: Callable[[Any], Any],
    _schema: type[BaseModel],
    input_payload: dict[str, Any],
) -> None:
    backend = FakeAgentBackend(
        responses=[{"unexpected": "shape"}, {"still": "invalid"}]
    )

    with pytest.raises(AgentOutputValidationError):
        await agent_cls(backend).run(input_payload)

    assert len(backend.calls) == 2


@pytest.mark.parametrize(
    ("agent_name", "agent_cls", "schema", "input_payload"), AGENT_CASES
)
@pytest.mark.asyncio
async def test_agent_retries_on_transient_error_then_succeeds(
    agent_name: str,
    agent_cls: Callable[[Any], Any],
    schema: type[BaseModel],
    input_payload: dict[str, Any],
) -> None:
    backend = FakeAgentBackend(
        responses=[VALID_RESPONSES[agent_name]],
        transient_errors_before_success=1,
    )

    result = await agent_cls(backend).run(input_payload)

    assert isinstance(result, schema)
    assert len(backend.calls) == 2


@pytest.mark.parametrize(
    ("_agent_name", "agent_cls", "_schema", "input_payload"), AGENT_CASES
)
@pytest.mark.asyncio
async def test_agent_does_not_retry_permanent_error(
    _agent_name: str,
    agent_cls: Callable[[Any], Any],
    _schema: type[BaseModel],
    input_payload: dict[str, Any],
) -> None:
    backend = FakeAgentBackend(permanent_error=True)

    with pytest.raises(PermanentError):
        await agent_cls(backend).run(input_payload)

    assert len(backend.calls) == 1


@pytest.mark.asyncio
async def test_planner_uses_current_node_registry_types_not_hardcoded_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(node_registry, "_REGISTRY", {})
    node_registry.register_node("temporary_extra_node")(NoOpSuccessHandler)
    backend = FakeAgentBackend(responses=[workflow_graph_response()])

    await PlannerAgent(backend).run(
        {
            "prompt": "Audit this GitHub repo",
            "repo_url": "https://github.com/example/project",
        }
    )

    assert (
        "temporary_extra_node"
        in backend.calls[0]["input_payload"]["available_node_types"]
    )


@pytest.mark.asyncio
async def test_planner_rejects_or_controls_unsupported_use_case() -> None:
    graph = await PlannerAgent(FakeAgentBackend()).run(
        {
            "prompt": "Schedule a calendar meeting",
            "repo_url": "https://github.com/example/project",
        }
    )

    assert len(graph.nodes) == 1
    assert graph.nodes[0].config["unsupported_use_case"] is True


@pytest.mark.asyncio
async def test_validator_pre_checks_with_domain_validate_and_sort_before_llm_call() -> (
    None
):
    backend = FakeAgentBackend(responses=[VALID_RESPONSES["validator"]])
    invalid_graph = {
        "nodes": [
            {
                "id": "A",
                "type": "manual_trigger",
                "name": "A",
                "config": {},
                "dependencies": ["B"],
            },
            {
                "id": "B",
                "type": "manual_trigger",
                "name": "B",
                "config": {},
                "dependencies": ["A"],
            },
        ]
    }

    result = await ValidatorAgent(backend).run({"graph": invalid_graph})

    assert result.valid is False
    assert result.issues
    assert backend.calls == []


@pytest.mark.asyncio
async def test_validator_detects_unsafe_write_without_approval() -> None:
    backend = FakeAgentBackend(responses=[VALID_RESPONSES["validator"]])
    graph = {
        "nodes": [
            {
                "id": "manual_trigger",
                "type": "manual_trigger",
                "name": "Manual Trigger",
                "config": {},
                "dependencies": [],
            },
            {
                "id": "github_issue_creator",
                "type": "github_issue_creator",
                "name": "Create Issues",
                "config": {},
                "dependencies": ["manual_trigger"],
            },
        ]
    }

    result = await ValidatorAgent(backend).run({"graph": graph})

    assert result.valid is True
    assert result.corrected_graph is not None
    approval = result.corrected_graph.nodes[1]
    issue_creator = result.corrected_graph.nodes[2]
    assert approval.type == "human_approval"
    assert approval.dependencies == ["manual_trigger"]
    assert issue_creator.dependencies == [approval.id]
    assert backend.calls == []


def test_repo_analyzer_output_schema_rejects_invalid_category() -> None:
    payload = VALID_RESPONSES["repo_analyzer"] | {
        "findings": [
            VALID_RESPONSES["repo_analyzer"]["findings"][0] | {"category": "sales"}
        ]
    }

    with pytest.raises(ValidationError):
        RepoAnalyzerOutput.model_validate(payload)


def test_readme_reviewer_score_bounds_are_enforced() -> None:
    payload = VALID_RESPONSES["readme_reviewer"] | {"quality_score": 101}

    with pytest.raises(ValidationError):
        ReadmeReviewerOutput.model_validate(payload)


def test_issue_generator_rejects_invalid_priority() -> None:
    issue = VALID_RESPONSES["issue_generator"]["issues"][0] | {"priority": "urgent"}
    payload = {"issues": [issue]}

    with pytest.raises(ValidationError):
        IssueGeneratorOutput.model_validate(payload)


def test_linkedin_draft_agent_does_not_claim_publish_action() -> None:
    payload = VALID_RESPONSES["linkedin_draft"] | {
        "post_text": "I published this automatically to LinkedIn."
    }

    with pytest.raises(ValidationError):
        LinkedInDraftOutput.model_validate(payload)


def test_agent_prompt_files_are_not_placeholders() -> None:
    prompt_root = Path(__file__).resolve().parents[2] / "app" / "agents" / "prompts"
    prompt_files = sorted(prompt_root.glob("*/v1.md"))

    assert {path.parent.name for path in prompt_files} == {
        "planner",
        "validator",
        "executor",
        "repo_analyzer",
        "readme_reviewer",
        "issue_generator",
        "linkedin_draft",
    }
    for prompt_file in prompt_files:
        text = prompt_file.read_text(encoding="utf-8")
        assert "TODO" not in text
        assert "You are an agent" not in text
        assert len(text.split()) >= 80
        for required_heading in [
            "Role:",
            "Input expectations:",
            "Output discipline:",
            "Safety rules:",
            "Missing data behavior:",
            "Mock/real honesty:",
            "Professional tone:",
        ]:
            assert required_heading in text


@pytest.mark.parametrize(
    ("agent_name", "_agent_cls", "schema", "_input_payload"), AGENT_CASES
)
def test_agent_output_schemas_reject_extra_fields_where_appropriate(
    agent_name: str,
    _agent_cls: Callable[[Any], Any],
    schema: type[BaseModel],
    _input_payload: dict[str, Any],
) -> None:
    payload = VALID_RESPONSES[agent_name] | {"extra": "not allowed"}

    with pytest.raises(ValidationError):
        schema.model_validate(payload)
