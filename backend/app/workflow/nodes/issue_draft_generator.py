from typing import ClassVar

from pydantic import BaseModel

from app.agents.issue_generator_agent import IssueGeneratorAgent
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
    completed,
    dependency_outputs,
    log_node,
    run_controlled,
)


@register_node("issue_draft_generator")
class IssueDraftGeneratorHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        findings = collect_dependency_values(context, "findings")
        warning_or_critical = [
            finding
            for finding in findings
            if isinstance(finding, dict)
            and finding.get("severity") in {"warning", "critical"}
        ]
        if not warning_or_critical:
            log_node(context, "issue_draft_generator_no_issues_needed")
            return completed({"issues": [], "issue_drafts": []})

        async def generate() -> dict:
            result = await IssueGeneratorAgent().run(
                {
                    "findings": warning_or_critical,
                    "context": dependency_outputs(context),
                }
            )
            return result.model_dump(mode="json")

        result = await run_controlled(
            context,
            generate,
            failure_code="issue_draft_generator_failed",
            failure_message="Issue draft generation failed in a controlled way.",
        )
        if isinstance(result, NodeExecutionResult):
            return result
        issues = result.get("issues", [])
        log_node(context, "issue_draft_generator_completed", issue_count=len(issues))
        return completed({"issues": issues, "issue_drafts": issues})
