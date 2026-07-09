
import pytest

import app.workflow.nodes  # noqa: F401
from app.agents.errors import AgentOutputValidationError
from app.mcp.exceptions import ToolCallError
from app.mcp.ports import ClientMode
from app.workflow.graph import NodeDefinition, WorkflowGraph
from app.workflow.node_registry import registered_node_types
from app.workflow.nodes.ai_repo_analyzer import AiRepoAnalyzerHandler
from app.workflow.nodes.condition import ConditionHandler
from app.workflow.nodes.github_issue_creator import GitHubIssueCreatorHandler
from app.workflow.nodes.github_repo_reader import GitHubRepoReaderHandler
from app.workflow.nodes.human_approval import HumanApprovalHandler
from app.workflow.nodes.issue_draft_generator import IssueDraftGeneratorHandler
from app.workflow.nodes.linkedin_draft_generator import LinkedInDraftGeneratorHandler
from app.workflow.nodes.manual_trigger import ManualTriggerHandler
from app.workflow.nodes.markdown_report_writer import MarkdownReportWriterHandler
from app.workflow.nodes.readme_reviewer import ReadmeReviewerHandler
from app.workflow.nodes.base import NodeExecutionContext
from app.workflow.state import NodeStatus, create_run_state


def ctx(
    node_type: str,
    inputs: dict | None = None,
    *,
    dependencies: dict[str, dict] | None = None,
) -> NodeExecutionContext:
    node = NodeDefinition(
        id=node_type,
        type=node_type,
        name=node_type,
        dependencies=list((dependencies or {}).keys()),
    )
    graph = WorkflowGraph(
        nodes=[
            *[
                NodeDefinition(id=dep, type="manual_trigger", name=dep)
                for dep in (dependencies or {})
            ],
            node,
        ]
    )
    run_state = create_run_state("run-1", graph)
    for dep, output in (dependencies or {}).items():
        run_state.node_states[dep].status = NodeStatus.COMPLETED
        run_state.node_states[dep].output = output
    return NodeExecutionContext(
        node=node,
        run_state=run_state,
        input_payload={**(inputs or {}), "_dependencies": dependencies or {}},
    )


@pytest.mark.asyncio
async def test_manual_trigger_success() -> None:
    result = await ManualTriggerHandler().execute(
        ctx(
            "manual_trigger",
            {"source_prompt": "Audit", "repo_url": "https://github.com/example/repo"},
        )
    )
    assert result.status == "completed"
    assert result.output["source_prompt"] == "Audit"
    assert result.output["repo_url"] == "https://github.com/example/repo"


@pytest.mark.asyncio
async def test_github_repo_reader_success_mock() -> None:
    result = await GitHubRepoReaderHandler().execute(
        ctx(
            "github_repo_reader",
            dependencies={
                "manual_trigger": {
                    "repo_url": "https://github.com/qurbaneliii/mock-repo"
                }
            },
        )
    )
    assert result.status == "completed"
    assert result.output["repo_snapshot"]["mode"] == "mock"


@pytest.mark.asyncio
async def test_github_repo_reader_failure_becomes_node_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingClient:
        mode = ClientMode.MOCK

        async def get_repo_snapshot(self, repo_url: str) -> dict:
            raise ToolCallError("get_repo_snapshot", "boom")

    monkeypatch.setattr(
        "app.workflow.nodes.github_repo_reader.get_client", lambda _: FailingClient()
    )
    result = await GitHubRepoReaderHandler().execute(
        ctx("github_repo_reader", {"repo_url": "https://github.com/example/repo"})
    )
    assert result.status == "failed"
    assert result.error["code"] == "github_repo_reader_failed"


@pytest.mark.asyncio
async def test_github_repo_reader_timeout_becomes_node_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.workflow.exceptions import NodeTimeoutError

    async def timeout(*args, **kwargs):
        raise NodeTimeoutError(0.01)

    monkeypatch.setattr("app.workflow.nodes.common.with_timeout", timeout)
    result = await GitHubRepoReaderHandler().execute(
        ctx("github_repo_reader", {"repo_url": "https://github.com/example/repo"})
    )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_repo_analyzer_success() -> None:
    result = await AiRepoAnalyzerHandler().execute(
        ctx(
            "ai_repo_analyzer",
            dependencies={"reader": {"repo_snapshot": {"readme": "# Hi"}}},
        )
    )
    assert result.status == "completed"
    assert result.output["summary"]


@pytest.mark.asyncio
async def test_repo_analyzer_agent_validation_failure_becomes_node_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BadAgent:
        async def run(self, payload: dict) -> dict:
            raise AgentOutputValidationError("repo_analyzer", "bad")

    monkeypatch.setattr(
        "app.workflow.nodes.ai_repo_analyzer.RepoAnalyzerAgent", lambda: BadAgent()
    )
    result = await AiRepoAnalyzerHandler().execute(
        ctx(
            "ai_repo_analyzer",
            dependencies={"reader": {"repo_snapshot": {"readme": "# Hi"}}},
        )
    )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_readme_reviewer_success() -> None:
    result = await ReadmeReviewerHandler().execute(
        ctx("readme_reviewer", {"readme": "# App"})
    )
    assert result.status == "completed"
    assert result.output["quality_score"] >= 0


@pytest.mark.asyncio
async def test_readme_reviewer_missing_readme() -> None:
    result = await ReadmeReviewerHandler().execute(
        ctx("readme_reviewer", {"repo_snapshot": {}})
    )
    assert result.status == "completed"
    assert result.output["quality_score"] == 0
    assert result.output["findings"][0]["title"] == "README is missing"


@pytest.mark.asyncio
async def test_issue_draft_generator_success() -> None:
    findings = [
        {
            "severity": "warning",
            "title": "Docs",
            "description": "x",
            "recommendation": "y",
        }
    ]
    result = await IssueDraftGeneratorHandler().execute(
        ctx("issue_draft_generator", dependencies={"analysis": {"findings": findings}})
    )
    assert result.status == "completed"
    assert result.output["issues"]


@pytest.mark.asyncio
async def test_issue_draft_generator_zero_findings() -> None:
    result = await IssueDraftGeneratorHandler().execute(
        ctx("issue_draft_generator", dependencies={"analysis": {"findings": []}})
    )
    assert result.status == "completed"
    assert result.output["issues"] == []


@pytest.mark.asyncio
async def test_human_approval_pauses() -> None:
    result = await HumanApprovalHandler().execute(ctx("human_approval"))
    assert result.status == "waiting_for_approval"


@pytest.mark.asyncio
async def test_human_approval_creates_approval_record() -> None:
    result = await HumanApprovalHandler().execute(
        ctx(
            "human_approval",
            dependencies={
                "drafts": {"issue_drafts": [{"title": "Fix", "priority": "high"}]}
            },
        )
    )
    assert result.output["issue_drafts"][0]["title"] == "Fix"
    assert result.output["risk_level"] == "high"


@pytest.mark.asyncio
async def test_github_issue_creator_requires_approval() -> None:
    result = await GitHubIssueCreatorHandler().execute(ctx("github_issue_creator"))
    assert result.status == "failed"
    assert result.error["code"] == "approval_required"


@pytest.mark.asyncio
async def test_github_issue_creator_rejects_missing_approval() -> None:
    result = await GitHubIssueCreatorHandler().execute(
        ctx(
            "github_issue_creator",
            dependencies={"approval": {"approval_status": "pending"}},
        )
    )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_github_issue_creator_rejects_rejected_approval() -> None:
    result = await GitHubIssueCreatorHandler().execute(
        ctx(
            "github_issue_creator",
            dependencies={
                "approval": {"decision": "rejected", "approval_summary": "No"}
            },
        )
    )
    assert result.status == "failed"
    assert result.error["code"] == "approval_rejected"


@pytest.mark.asyncio
async def test_github_issue_creator_idempotency() -> None:
    approval = {
        "decision": "approved",
        "approval_summary": "Yes",
        "target_repository": "https://github.com/qurbaneliii/mock-repo",
        "issue_drafts": [{"title": "Fix README", "body": "Body", "labels": []}],
    }
    first = await GitHubIssueCreatorHandler().execute(
        ctx("github_issue_creator", dependencies={"approval": approval})
    )
    second = await GitHubIssueCreatorHandler().execute(
        ctx("github_issue_creator", dependencies={"approval": approval})
    )
    assert (
        first.output["created_issues"][0]["idempotency_key"]
        == second.output["created_issues"][0]["idempotency_key"]
    )


@pytest.mark.asyncio
async def test_github_issue_creator_mock_mode_explicit() -> None:
    approval = {
        "decision": "approved",
        "approval_summary": "Yes",
        "target_repository": "https://github.com/qurbaneliii/mock-repo",
        "issue_drafts": [{"title": "Fix README", "body": "Body", "labels": []}],
    }
    result = await GitHubIssueCreatorHandler().execute(
        ctx("github_issue_creator", dependencies={"approval": approval})
    )
    assert result.output["mode"] == "mock"
    assert result.output["created_issues"][0]["display_url"].startswith("mock:")


@pytest.mark.asyncio
async def test_linkedin_draft_generator_success() -> None:
    result = await LinkedInDraftGeneratorHandler().execute(
        ctx("linkedin_draft_generator")
    )
    assert result.status == "completed"
    assert result.output["published"] is False


@pytest.mark.asyncio
async def test_linkedin_draft_generator_never_publishes() -> None:
    result = await LinkedInDraftGeneratorHandler().execute(
        ctx("linkedin_draft_generator", {"publish": True})
    )
    assert result.status == "failed"
    assert result.error["code"] == "publish_not_allowed"


@pytest.mark.asyncio
async def test_markdown_report_writer_persists_artifacts() -> None:
    result = await MarkdownReportWriterHandler().execute(
        ctx(
            "markdown_report_writer",
            dependencies={"analysis": {"analysis": {"summary": "Ok", "findings": []}}},
        )
    )
    assert result.status == "completed"
    assert {artifact["filename"] for artifact in result.output["artifacts"]} == {
        "repo_audit_report.md",
        "README_improvement_plan.md",
        "github_issue_drafts.md",
        "linkedin_post_draft.md",
    }


@pytest.mark.asyncio
async def test_condition_true_branch() -> None:
    result = await ConditionHandler().execute(
        ctx("condition", {"expression": "score >= 80", "score": 90})
    )
    assert result.output["branch"] == "true"


@pytest.mark.asyncio
async def test_condition_false_branch() -> None:
    result = await ConditionHandler().execute(
        ctx("condition", {"expression": "score >= 80", "score": 70})
    )
    assert result.output["branch"] == "false"


@pytest.mark.parametrize(
    "expression",
    [
        "danger()",
        "user.name == 'x'",
        "__import__('os')",
        "open('x')",
        "[x for x in values]",
    ],
)
@pytest.mark.asyncio
async def test_condition_rejects_function_calls(expression: str) -> None:
    result = await ConditionHandler().execute(
        ctx("condition", {"expression": expression, "values": [1]})
    )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_condition_rejects_attribute_access() -> None:
    result = await ConditionHandler().execute(
        ctx("condition", {"expression": "repo.private"})
    )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_condition_rejects_imports() -> None:
    result = await ConditionHandler().execute(
        ctx("condition", {"expression": "__import__('os')"})
    )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_condition_rejects_unsafe_builtins() -> None:
    result = await ConditionHandler().execute(
        ctx("condition", {"expression": "len(items) > 0", "items": [1]})
    )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_condition_resolves_names_only_from_context() -> None:
    result = await ConditionHandler().execute(
        ctx("condition", {"expression": "missing_name == 1"})
    )
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_raw_agent_exception_converted_to_failed_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BadAgent:
        async def run(self, payload: dict) -> dict:
            raise RuntimeError("raw secret exception")

    monkeypatch.setattr(
        "app.workflow.nodes.linkedin_draft_generator.LinkedInDraftAgent",
        lambda: BadAgent(),
    )
    result = await LinkedInDraftGeneratorHandler().execute(
        ctx("linkedin_draft_generator")
    )
    assert result.status == "failed"
    assert "raw secret exception" not in result.error["message"]


@pytest.mark.asyncio
async def test_raw_mcp_exception_converted_to_failed_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BadClient:
        mode = ClientMode.MOCK

        async def get_repo_snapshot(self, repo_url: str) -> dict:
            raise RuntimeError("token leaked")

    monkeypatch.setattr(
        "app.workflow.nodes.github_repo_reader.get_client", lambda _: BadClient()
    )
    result = await GitHubRepoReaderHandler().execute(
        ctx("github_repo_reader", {"repo_url": "https://github.com/example/repo"})
    )
    assert result.status == "failed"
    assert "token leaked" not in result.error["message"]


def test_example_workflow_uses_only_registered_node_types() -> None:
    node_types = set(registered_node_types())
    required = {
        "manual_trigger",
        "github_repo_reader",
        "ai_repo_analyzer",
        "readme_reviewer",
        "issue_draft_generator",
        "condition",
        "human_approval",
        "github_issue_creator",
        "linkedin_draft_generator",
        "markdown_report_writer",
    }
    assert required.issubset(node_types)
