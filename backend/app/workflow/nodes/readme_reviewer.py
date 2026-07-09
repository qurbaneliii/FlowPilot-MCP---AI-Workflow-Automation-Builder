from typing import ClassVar

from pydantic import BaseModel

from app.agents.readme_reviewer_agent import ReadmeReviewerAgent
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
    first_dependency_value,
    log_node,
    run_controlled,
)


@register_node("readme_reviewer")
class ReadmeReviewerHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        repo_snapshot = (
            context.inputs.get("repo_snapshot")
            or first_dependency_value(context, "repo_snapshot")
            or {}
        )
        readme = context.inputs.get("readme")
        if readme is None and isinstance(repo_snapshot, dict):
            readme = repo_snapshot.get("readme")
        if not readme:
            output = {
                "quality_score": 0,
                "missing_sections": ["README.md"],
                "suggestions": [
                    "Add a README with overview, setup, usage, testing, deployment, and maintenance notes."
                ],
                "improved_outline": [
                    "Overview",
                    "Features",
                    "Setup",
                    "Environment",
                    "Usage",
                    "Testing",
                    "Deployment",
                    "Architecture",
                ],
                "findings": [
                    {
                        "severity": "critical",
                        "title": "README is missing",
                        "description": "No README content was available in the repository snapshot.",
                        "recommendation": "Create a README using the recommended outline.",
                    }
                ],
            }
            log_node(context, "readme_reviewer_missing_readme")
            return completed({"readme_review": output, **output})

        async def review() -> dict:
            result = await ReadmeReviewerAgent().run(
                {"readme": readme, "repo_snapshot": repo_snapshot}
            )
            return result.model_dump(mode="json")

        result = await run_controlled(
            context,
            review,
            failure_code="readme_reviewer_failed",
            failure_message="README review failed in a controlled way.",
        )
        if isinstance(result, NodeExecutionResult):
            return result
        log_node(
            context,
            "readme_reviewer_completed",
            quality_score=result.get("quality_score"),
        )
        return completed({"readme_review": result, **result})
