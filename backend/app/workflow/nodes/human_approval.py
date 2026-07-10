from typing import Any, ClassVar

from pydantic import BaseModel

from app.workflow.node_registry import register_node
from app.workflow.nodes.base import (
    NodeExecutionContext,
    NodeExecutionResult,
    NodeHandler,
)
from app.workflow.nodes.common import (
    EmptyInput,
    EmptyOutput,
    collect_dependency_values,
    dependency_outputs,
    find_repo_url,
    log_node,
)


@register_node("human_approval")
class HumanApprovalHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        issue_drafts = _issue_drafts(context)
        risk_level = _risk_level(issue_drafts, dependency_outputs(context))
        resume_node_id = str(
            context.inputs.get("resume_node_id")
            or context.inputs.get("node_to_resume_after_approval")
            or _first_downstream_node_id(context)
            or "github_issue_creator"
        )
        output = {
            "approval_status": "pending",
            "approval_summary": str(
                context.inputs.get("summary")
                or f"Approve creation of {len(issue_drafts)} GitHub issue draft(s)."
            ),
            "issue_drafts": issue_drafts,
            "target_repository": find_repo_url(context),
            "risk_level": risk_level,
            "downstream_action": str(
                context.inputs.get("downstream_action")
                or "Create GitHub issues from approved drafts."
            ),
            "node_to_resume_after_approval": resume_node_id,
        }
        log_node(
            context,
            "human_approval_waiting",
            issue_count=len(issue_drafts),
            risk_level=risk_level,
        )
        return NodeExecutionResult(status="waiting_for_approval", output=output)


def _issue_drafts(context: NodeExecutionContext) -> list[dict[str, Any]]:
    drafts = context.inputs.get("issue_drafts") or context.inputs.get("issues")
    if isinstance(drafts, list):
        return [draft for draft in drafts if isinstance(draft, dict)]
    collected = collect_dependency_values(context, "issue_drafts")
    if collected:
        return [draft for draft in collected if isinstance(draft, dict)]
    collected = collect_dependency_values(context, "issues")
    return [draft for draft in collected if isinstance(draft, dict)]


def _risk_level(
    issue_drafts: list[dict[str, Any]], outputs: dict[str, dict[str, Any]]
) -> str:
    priorities = {str(issue.get("priority")) for issue in issue_drafts}
    if "high" in priorities:
        return "high"
    risk_flags = []
    for output in outputs.values():
        flags = output.get("risk_flags")
        if isinstance(flags, list):
            risk_flags.extend(flags)
    if any(
        isinstance(flag, dict) and flag.get("severity") == "critical"
        for flag in risk_flags
    ):
        return "high"
    if issue_drafts:
        return "medium"
    return "low"


def _first_downstream_node_id(context: NodeExecutionContext) -> str | None:
    for node in context.run_state.graph.nodes:
        if context.node.id in node.dependencies:
            return node.id
    return None
