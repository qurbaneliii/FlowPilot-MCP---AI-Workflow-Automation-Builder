import hashlib
from typing import Any, ClassVar

from pydantic import BaseModel

from app.mcp.registry import get_client
from app.workflow.node_registry import register_node
from app.workflow.nodes.base import (
    NodeExecutionContext,
    NodeExecutionResult,
    NodeHandler,
)
from app.workflow.nodes.common import (
    EmptyInput,
    EmptyOutput,
    completed,
    dependency_outputs,
    failed,
    log_node,
    run_controlled,
)


@register_node("github_issue_creator")
class GitHubIssueCreatorHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        approval = _approval_output(context)
        if approval is None:
            return failed(
                "approval_required",
                "Approved human approval is required before creating GitHub issues.",
            )
        decision = approval.get("decision") or approval.get("approval_status")
        if decision in {None, "pending"}:
            return failed(
                "approval_required",
                "Approved human approval is required before creating GitHub issues.",
            )
        if decision == "rejected":
            return failed(
                "approval_rejected",
                "GitHub issue creation was rejected by the approval decision.",
            )
        if decision != "approved":
            return failed(
                "approval_required",
                "Approved human approval is required before creating GitHub issues.",
            )

        repo_url = approval.get("target_repository") or context.inputs.get("repo_url")
        if not isinstance(repo_url, str) or not repo_url:
            return failed(
                "missing_repo_url", "Target repository is required for issue creation."
            )
        issue_drafts = (
            approval.get("issue_drafts") or context.inputs.get("issue_drafts") or []
        )
        if not isinstance(issue_drafts, list):
            return failed("invalid_issue_drafts", "Issue drafts must be a list.")

        async def create() -> dict[str, Any]:
            client = get_client("github")
            created = []
            for issue in issue_drafts:
                if not isinstance(issue, dict):
                    continue
                title = str(issue.get("title") or "Untitled issue")
                body = str(issue.get("body") or "")
                labels = [
                    str(label)
                    for label in issue.get("labels", [])
                    if isinstance(label, str)
                ]
                key = _idempotency_key(context.run_state.run_id, context.node.id, title)
                result = await client.create_issue(  # type: ignore[attr-defined]
                    repo_url=repo_url,
                    title=title,
                    body=body,
                    labels=labels,
                    idempotency_key=key,
                )
                if not result.success:
                    raise RuntimeError("GitHub issue creation failed")
                url = str((result.data or {}).get("url") or "")
                created.append(
                    {
                        "title": title,
                        "url": url,
                        "display_url": f"mock:{url}" if client.is_mock else url,
                        "idempotency_key": key,
                        "mode": client.mode.value,
                    }
                )
            return {
                "created_issues": created,
                "mode": client.mode.value,
                "mock": client.is_mock,
            }

        result = await run_controlled(
            context,
            create,
            failure_code="github_issue_creator_failed",
            failure_message="GitHub issue creation failed in a controlled way.",
        )
        if isinstance(result, NodeExecutionResult):
            return result
        log_node(
            context,
            "github_issue_creator_completed",
            created_count=len(result["created_issues"]),
            mode=result["mode"],
        )
        return completed(result)


def _approval_output(context: NodeExecutionContext) -> dict[str, Any] | None:
    for output in dependency_outputs(context).values():
        if (
            "approval_summary" in output
            or "approval_status" in output
            or "decision" in output
        ):
            return output
    approval = context.inputs.get("approval")
    return approval if isinstance(approval, dict) else None


def _idempotency_key(run_id: str, node_id: str, title: str) -> str:
    digest = hashlib.sha256(f"{run_id}:{node_id}:{title}".encode("utf-8")).hexdigest()
    return f"{run_id}:{node_id}:{digest[:16]}"
