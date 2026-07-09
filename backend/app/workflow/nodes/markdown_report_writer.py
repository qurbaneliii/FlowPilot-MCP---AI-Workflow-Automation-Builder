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
    completed,
    dependency_outputs,
    first_dependency_value,
    make_artifact,
    log_node,
)


@register_node("markdown_report_writer")
class MarkdownReportWriterHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        outputs = dependency_outputs(context)
        mode = _mode(outputs)
        analysis = first_dependency_value(context, "analysis") or {}
        readme_review = first_dependency_value(context, "readme_review") or {}
        issue_drafts = collect_dependency_values(context, "issue_drafts")
        created_issues = collect_dependency_values(context, "created_issues")
        linkedin = first_dependency_value(context, "linkedin_draft") or {}
        artifacts = [
            make_artifact(
                run_id=context.run_state.run_id,
                artifact_type="repo_audit_report",
                filename="repo_audit_report.md",
                content=_repo_report(analysis, readme_review, created_issues),
                mode=mode,
                source_node_id=context.node.id,
            ),
            make_artifact(
                run_id=context.run_state.run_id,
                artifact_type="readme_improvement_plan",
                filename="README_improvement_plan.md",
                content=_readme_plan(readme_review),
                mode=mode,
                source_node_id=context.node.id,
            ),
            make_artifact(
                run_id=context.run_state.run_id,
                artifact_type="github_issue_drafts",
                filename="github_issue_drafts.md",
                content=_issue_drafts(issue_drafts, created_issues),
                mode=mode,
                source_node_id=context.node.id,
            ),
            make_artifact(
                run_id=context.run_state.run_id,
                artifact_type="linkedin_post_draft",
                filename="linkedin_post_draft.md",
                content=_linkedin_draft(linkedin),
                mode=mode,
                source_node_id=context.node.id,
            ),
        ]
        log_node(
            context,
            "markdown_report_writer_completed",
            artifact_count=len(artifacts),
            mode=mode,
        )
        return completed({"artifacts": artifacts})


def _mode(outputs: dict[str, dict[str, Any]]) -> str | None:
    for output in outputs.values():
        mode = output.get("mode")
        if isinstance(mode, str):
            return mode
    return None


def _repo_report(analysis: Any, readme_review: Any, created_issues: list[Any]) -> str:
    findings = analysis.get("findings", []) if isinstance(analysis, dict) else []
    summary = (
        analysis.get("summary", "No analysis summary available.")
        if isinstance(analysis, dict)
        else "No analysis summary available."
    )
    return "\n".join(
        [
            "# Repository Audit Report",
            "",
            f"Summary: {summary}",
            "",
            f"Findings: {len(findings)}",
            f"README score: {readme_review.get('quality_score', 'n/a') if isinstance(readme_review, dict) else 'n/a'}",
            f"Created issues: {len(created_issues)}",
        ]
    )


def _readme_plan(readme_review: Any) -> str:
    if not isinstance(readme_review, dict):
        return "# README Improvement Plan\n\nNo README review was available."
    outline = "\n".join(
        f"- {item}" for item in readme_review.get("improved_outline", [])
    )
    suggestions = "\n".join(
        f"- {item}" for item in readme_review.get("suggestions", [])
    )
    return f"# README Improvement Plan\n\n## Recommended Outline\n{outline}\n\n## Suggestions\n{suggestions}\n"


def _issue_drafts(issue_drafts: list[Any], created_issues: list[Any]) -> str:
    lines = ["# GitHub Issue Drafts", ""]
    if not issue_drafts:
        lines.append("No warning or critical findings required GitHub issue drafts.")
    for issue in issue_drafts:
        if isinstance(issue, dict):
            lines.extend(
                [
                    f"## {issue.get('title', 'Untitled')}",
                    "",
                    str(issue.get("body", "")),
                    "",
                ]
            )
    if created_issues:
        lines.extend(["## Creation Results", ""])
        for issue in created_issues:
            if isinstance(issue, dict):
                lines.append(
                    f"- {issue.get('title')}: {issue.get('display_url') or issue.get('url')}"
                )
    return "\n".join(lines)


def _linkedin_draft(linkedin: Any) -> str:
    if not isinstance(linkedin, dict):
        return "# LinkedIn Post Draft\n\nNo draft was generated."
    hashtags = " ".join(linkedin.get("hashtags", []))
    return f"# LinkedIn Post Draft\n\n{linkedin.get('post_text', '')}\n\n{hashtags}\n"
