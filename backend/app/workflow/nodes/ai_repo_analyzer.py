from typing import ClassVar

from pydantic import BaseModel

from app.agents.repo_analyzer_agent import RepoAnalyzerAgent
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
    failed,
    first_dependency_value,
    log_node,
    run_controlled,
)


@register_node("ai_repo_analyzer")
class AiRepoAnalyzerHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        repo_snapshot = context.inputs.get("repo_snapshot") or first_dependency_value(
            context, "repo_snapshot"
        )
        if not isinstance(repo_snapshot, dict):
            return failed("missing_repo_snapshot", "Repository snapshot is required.")

        async def analyze() -> dict:
            result = await RepoAnalyzerAgent().run(
                {
                    "repo_snapshot": repo_snapshot,
                    "analysis_dimensions": [
                        "documentation",
                        "setup",
                        "environment",
                        "testing",
                        "ci_cd",
                        "structure",
                        "security_hygiene",
                        "deployment_readiness",
                        "maintainability",
                        "portfolio_recruiter_readiness",
                    ],
                }
            )
            return result.model_dump(mode="json")

        result = await run_controlled(
            context,
            analyze,
            failure_code="repo_analyzer_failed",
            failure_message="Repository analysis failed in a controlled way.",
        )
        if isinstance(result, NodeExecutionResult):
            return result
        log_node(
            context,
            "ai_repo_analyzer_completed",
            finding_count=len(result.get("findings", [])),
        )
        return completed({"analysis": result, **result})
