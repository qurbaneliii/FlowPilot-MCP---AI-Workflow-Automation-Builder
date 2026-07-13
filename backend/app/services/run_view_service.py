from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas.run import (
    ApprovalIssuePreviewResponse,
    ApprovalPanelResponse,
    ArtifactResponse,
    ArtifactTabResponse,
    NodeResultSummaryResponse,
    NodeRunResponse,
    PendingApprovalResponse,
    RunSummaryResponse,
    RunTimelineEntryResponse,
    RunUiBannerResponse,
    RunUiStateResponse,
)
from app.schemas.ui import (
    CompletionIssueCreationResponse,
    CompletionOutputResponse,
    CompletionSummaryResponse,
    GuidedStepResponse,
    GuidedStepsResponse,
    NextActionResponse,
    WorkflowReviewResponse,
    WorkflowReviewWriteResponse,
)
from app.schemas.workflow_graph import (
    WorkflowLayoutNodeResponse,
    WorkflowLayoutResponse,
    WorkflowNodeDisplayResponse,
    WorkflowSummaryResponse,
)
from app.services.store import STORE
from app.workflow.graph import NodeDefinition, WorkflowGraph
from app.workflow.state import NodeExecutionState, RunState


NODE_DISPLAY: dict[str, dict[str, str]] = {
    "manual_trigger": {
        "subtitle": "Trigger",
        "icon": "trigger",
        "description": "Starts the workflow from the user prompt and repository URL.",
    },
    "github_repo_reader": {
        "subtitle": "Repository scan",
        "icon": "github",
        "description": "Reads repository metadata, README content, and file tree details.",
    },
    "ai_repo_analyzer": {
        "subtitle": "AI analysis",
        "icon": "ai",
        "description": "Reviews repository quality, risks, and improvement opportunities.",
    },
    "readme_reviewer": {
        "subtitle": "README review",
        "icon": "document",
        "description": "Scores README quality and suggests missing documentation sections.",
    },
    "issue_draft_generator": {
        "subtitle": "Issue drafts",
        "icon": "issue",
        "description": "Drafts guarded GitHub issues from warning and critical findings.",
    },
    "human_approval": {
        "subtitle": "Approval gate",
        "icon": "approval",
        "description": "Pauses before any external GitHub issue creation.",
    },
    "github_issue_creator": {
        "subtitle": "Issue creation",
        "icon": "github",
        "description": "Creates or simulates GitHub issues after approval.",
    },
    "linkedin_draft_generator": {
        "subtitle": "LinkedIn draft",
        "icon": "linkedin",
        "description": "Drafts a LinkedIn-ready demo update from the audit result.",
    },
    "markdown_report_writer": {
        "subtitle": "Reports",
        "icon": "report",
        "description": "Writes reviewable markdown artifacts for the completed run.",
    },
    "condition": {
        "subtitle": "Condition",
        "icon": "condition",
        "description": "Routes execution based on workflow state.",
    },
}

ARTIFACT_TYPES = (
    "repo_audit_report",
    "readme_improvement_plan",
    "github_issue_drafts",
    "linkedin_post_draft",
)

ARTIFACT_LABELS = {
    "repo_audit_report": "Repo Audit Report",
    "readme_improvement_plan": "README Improvement Plan",
    "github_issue_drafts": "GitHub Issue Drafts",
    "linkedin_post_draft": "LinkedIn Draft",
}

GUIDED_STEP_DEFINITIONS = (
    (
        "define_task",
        "Define Task",
        "The automation request and repository URL were provided.",
    ),
    (
        "generate_workflow",
        "Generate Workflow",
        "FlowPilot created an executable workflow graph.",
    ),
    (
        "run_automation",
        "Run Automation",
        "Workflow nodes are reading and analyzing the repository.",
    ),
    (
        "review_approval",
        "Review Approval",
        "GitHub issue creation waits for a human decision.",
    ),
    (
        "view_outputs",
        "View Outputs",
        "Generated reports and drafts are ready to review.",
    ),
)


class RunViewService:
    def generated_guided_steps(self) -> GuidedStepsResponse:
        return _guided_steps("run_automation", completed_through=1)

    def generated_next_action(self) -> NextActionResponse:
        return NextActionResponse(
            title="Run the automation",
            description="Review the generated workflow, then start the run.",
            primary_label="Run automation",
            target_tab="canvas",
            severity="info",
        )

    def workflow_review(self, graph: WorkflowGraph) -> WorkflowReviewResponse:
        approval_required = any(node.type == "human_approval" for node in graph.nodes)
        return WorkflowReviewResponse(
            title="GitHub Repository Audit",
            plain_english_summary=(
                "FlowPilot will read the repository, analyze documentation and project structure, "
                "draft GitHub issues, request approval before writes, and generate final reports."
            ),
            reads=[
                "Repository metadata",
                "README",
                "File tree",
                "Package files",
                "Test files",
                "CI configuration",
            ],
            writes=[
                WorkflowReviewWriteResponse(
                    label="GitHub issues",
                    requires_approval=approval_required,
                    mode="mock_or_real",
                )
            ],
            approval_required=approval_required,
            risk_level="medium" if approval_required else "low",
            estimated_outputs=list(ARTIFACT_LABELS.values()),
        )

    def guided_steps(self, run_state: RunState) -> GuidedStepsResponse:
        if run_state.status == "waiting_for_approval":
            return _guided_steps("review_approval", completed_through=2)
        if run_state.status == "completed":
            return _guided_steps("view_outputs", completed_through=4)
        if run_state.status == "failed":
            failed_node = next(
                (
                    node
                    for node in run_state.graph.nodes
                    if run_state.node_states.get(node.id)
                    and run_state.node_states[node.id].status == "failed"
                ),
                None,
            )
            failed_step = (
                "review_approval"
                if failed_node is not None and failed_node.type == "human_approval"
                else "run_automation"
            )
            return _guided_steps(
                failed_step,
                completed_through=2 if failed_step == "review_approval" else 1,
                failed_step=failed_step,
            )
        return _guided_steps("run_automation", completed_through=1)

    def next_action(self, run_state: RunState) -> NextActionResponse:
        if run_state.status == "waiting_for_approval":
            return NextActionResponse(
                title="Human approval required",
                description="Review issue drafts before GitHub issue creation.",
                primary_label="Approve issue creation",
                secondary_label="Reject and skip issues",
                target_tab="approval",
                target_node_id="human_approval",
                severity="warning",
            )
        if run_state.status == "completed":
            return NextActionResponse(
                title="Review generated outputs",
                description="FlowPilot generated audit reports, issue drafts, and a LinkedIn draft.",
                primary_label="View reports",
                target_tab="reports",
                severity="info",
            )
        if run_state.status == "failed":
            return NextActionResponse(
                title="Inspect failed node",
                description="Open logs to inspect the failed workflow step.",
                primary_label="Open logs",
                target_tab="logs",
                target_node_id=_active_node_id(run_state),
                severity="error",
            )
        return NextActionResponse(
            title="Workflow is running",
            description="FlowPilot is reading the repository and executing workflow nodes.",
            target_tab="canvas",
            target_node_id=_active_node_id(run_state),
            severity="info",
        )

    def completion_summary(
        self, run_state: RunState, artifacts: list[ArtifactResponse]
    ) -> CompletionSummaryResponse | None:
        if run_state.status != "completed":
            return None
        issue_state = run_state.node_states.get("github_issue_creator")
        issue_output = issue_state.output if issue_state and issue_state.output else {}
        created = issue_output.get("created_issues", [])
        created_count = len(created) if isinstance(created, list) else 0
        skipped = issue_state is not None and issue_state.status == "skipped"
        issue_mode = "skipped" if skipped else str(issue_output.get("mode") or "mock")
        if skipped:
            issue_message = (
                "GitHub issue creation was skipped. Reports were still generated."
            )
        elif issue_mode == "mock":
            issue_message = (
                "Issue creation ran in mock mode. No real GitHub issues were created."
            )
        else:
            issue_message = (
                f"{created_count} GitHub issues were created after approval."
            )
        available_types = {artifact.artifact_type for artifact in artifacts}
        primary_outputs = [
            CompletionOutputResponse(type=artifact_type, label=label)
            for artifact_type, label in ARTIFACT_LABELS.items()
            if artifact_type in available_types
        ]
        return CompletionSummaryResponse(
            title="Workflow completed",
            description=f"FlowPilot audited the repository and generated {len(artifacts)} artifacts.",
            artifact_count=len(artifacts),
            issue_creation=CompletionIssueCreationResponse(
                mode=issue_mode,
                created_count=created_count,
                message=issue_message,
            ),
            primary_outputs=primary_outputs,
        )

    def workflow_summary(
        self, graph: WorkflowGraph, *, repo_url: str | None, mode: str | None = "mock"
    ) -> WorkflowSummaryResponse:
        nodes = graph.nodes
        return WorkflowSummaryResponse(
            name="GitHub Repository Audit" if nodes else "No workflow generated",
            description=(
                "Audit a repository, draft guarded GitHub issues, and produce demo-ready artifacts."
                if nodes
                else "Generate a workflow to see the executable graph."
            ),
            repo_url=repo_url,
            node_count=len(nodes),
            estimated_stages=max(_stage_map(graph).values(), default=0),
            risky_action_count=sum(1 for node in nodes if _risk_level(node) != "none"),
            approval_required=any(node.type == "human_approval" for node in nodes),
            mode=mode,
            status_label="Validated",
        )

    def node_display(self, graph: WorkflowGraph) -> list[WorkflowNodeDisplayResponse]:
        stages = _stage_map(graph)
        return [
            _node_display_response(node, order=index + 1, stage=stages[node.id])
            for index, node in enumerate(graph.nodes)
        ]

    def layout(self, graph: WorkflowGraph) -> WorkflowLayoutResponse:
        stages = _stage_map(graph)
        return WorkflowLayoutResponse(
            direction="vertical",
            nodes=[
                WorkflowLayoutNodeResponse(
                    id=node.id,
                    x=0,
                    y=(stages[node.id] - 1) * 140,
                )
                for node in graph.nodes
            ],
        )

    def nodes(self, run_state: RunState) -> list[NodeRunResponse]:
        stages = _stage_map(run_state.graph)
        by_id = {node.id: node for node in run_state.graph.nodes}
        return [
            self._node_response(
                node=by_id[node_id],
                state=state,
                order=index + 1,
                stage=stages[node_id],
            )
            for index, (node_id, state) in enumerate(run_state.node_states.items())
            if node_id in by_id
        ]

    def run_summary(
        self,
        run_state: RunState,
        *,
        artifacts: list[ArtifactResponse],
        mode: str | None,
        started_at: datetime | None,
        completed_at: datetime | None,
    ) -> RunSummaryResponse:
        states = list(run_state.node_states.values())
        active_node_id = _active_node_id(run_state)
        return RunSummaryResponse(
            title="Workflow execution",
            repo_url=_repo_url(run_state),
            mode=mode,
            nodes_total=len(states),
            nodes_completed=sum(1 for state in states if state.status == "completed"),
            nodes_failed=sum(1 for state in states if state.status == "failed"),
            nodes_skipped=sum(1 for state in states if state.status == "skipped"),
            nodes_waiting=sum(
                1 for state in states if state.status == "waiting_for_approval"
            ),
            artifacts_count=len(artifacts),
            started_at=started_at,
            completed_at=completed_at,
            active_node_id=active_node_id,
            next_required_action=_next_required_action(run_state, active_node_id),
        )

    def timeline(self, run_state: RunState) -> list[RunTimelineEntryResponse]:
        by_id = {node.id: node for node in run_state.graph.nodes}
        entries: list[RunTimelineEntryResponse] = []
        for node_id, state in run_state.node_states.items():
            node = by_id.get(node_id)
            if node is None:
                continue
            entries.append(
                RunTimelineEntryResponse(
                    node_id=node_id,
                    name=node.name,
                    status=state.status.value,
                    timestamp=state.completed_at or state.started_at,
                    message=_timeline_message(node, state),
                    severity=_status_severity(state.status.value),
                )
            )
        return entries

    def pending_approval(self, run_state: RunState) -> PendingApprovalResponse | None:
        for approval_id, record in STORE.approvals.items():
            if record.run_id != run_state.run_id or record.status != "pending":
                continue
            node_id = STORE.approval_nodes[approval_id]
            output = run_state.node_states[node_id].output or {}
            return PendingApprovalResponse(
                approval_id=approval_id,
                status=record.status,
                node_id=node_id,
                approval_summary=output.get("approval_summary"),
                issue_drafts=output.get("issue_drafts", []),
                target_repository=output.get("target_repository"),
                risk_level=output.get("risk_level"),
                downstream_action=output.get("downstream_action"),
                node_to_resume_after_approval=output.get(
                    "node_to_resume_after_approval"
                ),
            )
        return None

    def approval_panel(
        self,
        approval: PendingApprovalResponse | None,
        *,
        mode: str | None,
    ) -> ApprovalPanelResponse | None:
        if approval is None:
            return None
        issue_previews = [
            ApprovalIssuePreviewResponse(
                title=str(issue.get("title") or "Untitled issue"),
                priority=(
                    str(issue.get("priority"))
                    if issue.get("priority") is not None
                    else None
                ),
                labels=[str(label) for label in issue.get("labels", [])],
                body_preview=str(issue.get("body") or "")[:180],
            )
            for issue in approval.issue_drafts
            if isinstance(issue, dict)
        ]
        return ApprovalPanelResponse(
            approval_id=approval.approval_id,
            status=approval.status,
            title="Human approval required",
            description="FlowPilot paused before creating GitHub issues.",
            target_action=approval.downstream_action or "GitHub issue creation",
            target_repository=approval.target_repository,
            mode=mode,
            risk_level=approval.risk_level,
            issue_count=len(approval.issue_drafts),
            issue_previews=issue_previews,
            issue_drafts=approval.issue_drafts,
            can_approve=approval.status == "pending",
            can_reject=approval.status == "pending",
        )

    def artifact_tabs(
        self, artifacts: list[ArtifactResponse]
    ) -> dict[str, ArtifactTabResponse]:
        latest = _latest_artifacts_by_type(artifacts)
        return {
            artifact_type: ArtifactTabResponse(
                available=artifact_type in latest,
                artifact_id=(
                    latest[artifact_type].artifact_id
                    if artifact_type in latest
                    else None
                ),
            )
            for artifact_type in ARTIFACT_TYPES
        }

    def node_results(self, run_state: RunState) -> list[NodeResultSummaryResponse]:
        return [
            _node_result_summary(node_id, state)
            for node_id, state in run_state.node_states.items()
        ]

    def ui_state(
        self,
        run_state: RunState,
        *,
        summary: RunSummaryResponse,
        approval: ApprovalPanelResponse | None,
    ) -> RunUiStateResponse:
        if run_state.status == "waiting_for_approval":
            return RunUiStateResponse(
                primary_view="approval",
                recommended_tab="approval",
                canvas_focus_node_id=(
                    _active_node_id(run_state)
                    if approval is not None
                    else summary.active_node_id
                ),
                show_approval_panel=True,
                banner=RunUiBannerResponse(
                    type="warning",
                    title="Human approval required",
                    message="Review issue drafts before GitHub issue creation.",
                ),
            )
        if run_state.status == "completed":
            return RunUiStateResponse(
                primary_view="reports",
                recommended_tab="reports",
                canvas_focus_node_id=summary.active_node_id,
                show_reports_panel=True,
                show_completion_summary=True,
                banner=RunUiBannerResponse(
                    type="success",
                    title="Reports ready",
                    message="Generated artifacts are ready for review.",
                ),
            )
        if run_state.status == "failed":
            return RunUiStateResponse(
                primary_view="logs",
                recommended_tab="logs",
                canvas_focus_node_id=summary.active_node_id,
                banner=RunUiBannerResponse(
                    type="error",
                    title="Run failed",
                    message=str(
                        (run_state.error or {}).get("message")
                        or "Review logs for details."
                    ),
                ),
            )
        return RunUiStateResponse(
            primary_view="canvas" if run_state.status == "running" else "overview",
            recommended_tab="overview",
            canvas_focus_node_id=summary.active_node_id,
        )

    def inspector(self, run_state: RunState) -> dict[str, Any]:
        return {
            node_id: {
                "summary": summary.summary,
                "metrics": summary.metrics,
            }
            for node_id, summary in (
                (item.node_id, item) for item in self.node_results(run_state)
            )
        }

    def _node_response(
        self,
        *,
        node: NodeDefinition,
        state: NodeExecutionState,
        order: int,
        stage: int,
    ) -> NodeRunResponse:
        node_display = _node_display_response(node, order=order, stage=stage)
        summary = _node_result_summary(node.id, state)
        status = _ui_node_status(node, state)
        return NodeRunResponse(
            node_id=node.id,
            id=node.id,
            type=node.type,
            name=node.name,
            subtitle=node_display.subtitle,
            status=status,
            order=order,
            stage=stage,
            dependencies=node.dependencies,
            output=state.output,
            error=state.error,
            retry_count=state.retry_count,
            started_at=state.started_at,
            completed_at=state.completed_at,
            duration_ms=_duration_ms(state),
            display={
                "icon": node_display.icon,
                "status_label": _status_label(status),
                "summary": summary.summary,
                "severity": _status_severity(status),
                "is_risky": node_display.risk_level != "none",
                "is_approval_gate": node.type == "human_approval",
            },
            output_summary=summary.model_dump(mode="json"),
        )


def _node_display_response(
    node: NodeDefinition, *, order: int, stage: int
) -> WorkflowNodeDisplayResponse:
    meta = NODE_DISPLAY.get(node.type, {})
    return WorkflowNodeDisplayResponse(
        id=node.id,
        type=node.type,
        name=node.name,
        subtitle=meta.get("subtitle", node.type.replace("_", " ").title()),
        icon=meta.get("icon", "condition"),
        order=order,
        stage=stage,
        dependencies=node.dependencies,
        risk_level=_risk_level(node),
        approval_required=node.type == "human_approval",
        description=meta.get("description", f"Executes {node.name}."),
    )


def _stage_map(graph: WorkflowGraph) -> dict[str, int]:
    by_id = {node.id: node for node in graph.nodes}
    cache: dict[str, int] = {}

    def stage(node: NodeDefinition) -> int:
        if node.id in cache:
            return cache[node.id]
        if not node.dependencies:
            cache[node.id] = 1
            return 1
        cache[node.id] = 1 + max(
            stage(by_id[dependency])
            for dependency in node.dependencies
            if dependency in by_id
        )
        return cache[node.id]

    for item in graph.nodes:
        stage(item)
    return cache


def _risk_level(node: NodeDefinition) -> str:
    if node.type == "github_issue_creator":
        return "medium"
    if node.type == "human_approval":
        return "medium"
    return "none"


def _mode(run_state: RunState) -> str | None:
    for state in run_state.node_states.values():
        output = state.output or {}
        mode = output.get("mode") if isinstance(output, dict) else None
        if isinstance(mode, str):
            return mode
        snapshot = output.get("repo_snapshot") if isinstance(output, dict) else None
        if isinstance(snapshot, dict) and isinstance(snapshot.get("mode"), str):
            return snapshot["mode"]
    return None


def _repo_url(run_state: RunState) -> str | None:
    workflow_id = STORE.run_workflows.get(run_state.run_id)
    workflow = STORE.workflows.get(workflow_id or "")
    if workflow is not None:
        return workflow.repo_url
    for state in run_state.node_states.values():
        output = state.output or {}
        if isinstance(output.get("repo_url"), str):
            return output["repo_url"]
    return None


def infer_mode(run_state: RunState) -> str | None:
    return _mode(run_state)


def _active_node_id(run_state: RunState) -> str | None:
    for status in ("waiting_for_approval", "running", "pending", "failed"):
        for node_id, state in run_state.node_states.items():
            if state.status == status:
                return node_id
    return (
        next(reversed(run_state.node_states), None) if run_state.node_states else None
    )


def _next_required_action(
    run_state: RunState, active_node_id: str | None
) -> str | None:
    if run_state.status == "waiting_for_approval":
        return "Approve GitHub issue creation"
    if run_state.status == "failed":
        return "Review run logs"
    if run_state.status == "completed":
        return "Review generated artifacts"
    if active_node_id:
        return f"Waiting on {active_node_id.replace('_', ' ')}"
    return None


def _timeline_message(node: NodeDefinition, state: NodeExecutionState) -> str:
    if state.status == "waiting_for_approval":
        return "Waiting for human approval."
    if state.status == "completed":
        return f"{node.name} completed."
    if state.status == "failed":
        return str((state.error or {}).get("message") or f"{node.name} failed.")
    if state.status == "skipped":
        return f"{node.name} skipped."
    if state.status == "running":
        return f"{node.name} running."
    return f"{node.name} pending."


def _status_label(status: str) -> str:
    return {
        "pending": "Pending",
        "running": "Running",
        "completed": "Completed",
        "failed": "Failed",
        "waiting_for_approval": "Waiting for approval",
        "skipped": "Skipped",
    }.get(status, status.replace("_", " ").title())


def _status_severity(status: str) -> str:
    return {
        "completed": "success",
        "waiting_for_approval": "warning",
        "failed": "error",
        "skipped": "info",
        "running": "info",
        "pending": "info",
    }.get(status, "info")


def _duration_ms(state: NodeExecutionState) -> int | None:
    if not state.started_at or not state.completed_at:
        return None
    return int((state.completed_at - state.started_at).total_seconds() * 1000)


def _ui_node_status(node: NodeDefinition, state: NodeExecutionState) -> str:
    if node.type == "github_issue_creator":
        return state.status.value
    return state.status.value


def _node_result_summary(
    node_id: str, state: NodeExecutionState
) -> NodeResultSummaryResponse:
    output = state.output or {}
    if state.error:
        return NodeResultSummaryResponse(
            node_id=node_id,
            title="Node failed",
            summary=str(state.error.get("message") or "Node failed."),
            metrics={"status": state.status.value},
        )
    if node_id == "manual_trigger":
        repo_url = str(output.get("repo_url") or "Repository captured")
        display_repo = repo_url.removeprefix("https://")
        return NodeResultSummaryResponse(
            node_id=node_id,
            title="Workflow triggered",
            summary=f"Started from your prompt for {display_repo}.",
            metrics={"repo_url": output.get("repo_url")},
        )
    if node_id == "github_repo_reader":
        snapshot = output.get("repo_snapshot") if isinstance(output, dict) else {}
        snapshot = snapshot if isinstance(snapshot, dict) else {}
        files = snapshot.get("file_tree") or snapshot.get("tree") or []
        file_count = len(files) if isinstance(files, list) else 0
        readme_found = bool(snapshot.get("readme"))
        mode = str(output.get("mode") or snapshot.get("mode") or "pending")
        mode_label = "Real GitHub read" if mode == "real" else "Safe mock read"
        return NodeResultSummaryResponse(
            node_id=node_id,
            title="Repository scanned",
            summary=f"Scanned {file_count} files. README {'found' if readme_found else 'not found'}. {mode_label} mode.",
            metrics={
                "files_scanned": file_count,
                "readme_found": readme_found,
                "mode": mode,
            },
        )
    if node_id == "ai_repo_analyzer":
        findings = (
            output.get("findings") if isinstance(output.get("findings"), list) else []
        )
        warning_count = sum(
            1 for finding in findings if _dict_value(finding, "severity") == "warning"
        )
        critical_count = sum(
            1 for finding in findings if _dict_value(finding, "severity") == "critical"
        )
        info_count = sum(
            1 for finding in findings if _dict_value(finding, "severity") == "info"
        )
        return NodeResultSummaryResponse(
            node_id=node_id,
            title="Repository analyzed",
            summary=f"Generated {len(findings)} findings: {critical_count} critical, {warning_count} warnings, {info_count} info.",
            metrics={
                "findings": len(findings),
                "warning_count": warning_count,
                "critical_count": critical_count,
                "info_count": info_count,
            },
        )
    if node_id == "readme_reviewer":
        missing = (
            output.get("missing_sections")
            if isinstance(output.get("missing_sections"), list)
            else []
        )
        score = output.get("quality_score", "n/a")
        return NodeResultSummaryResponse(
            node_id=node_id,
            title="README reviewed",
            summary=f"README score: {score}/100. Missing {len(missing)} recommended sections.",
            metrics={"readme_score": score, "missing_sections": len(missing)},
        )
    if node_id == "issue_draft_generator":
        drafts = output.get("issue_drafts") or output.get("issues") or []
        draft_count = len(drafts) if isinstance(drafts, list) else 0
        return NodeResultSummaryResponse(
            node_id=node_id,
            title="Issue drafts prepared",
            summary=f"Generated {draft_count} issue drafts.",
            metrics={"issue_drafts": draft_count},
        )
    if node_id == "human_approval":
        drafts = output.get("issue_drafts") or []
        risk = output.get("risk_level") or "medium"
        status = output.get("decision") or state.status.value
        issue_count = len(drafts) if isinstance(drafts, list) else 0
        if state.status == "waiting_for_approval":
            summary = f"Waiting for approval to create {issue_count} GitHub issues."
        else:
            summary = (
                f"Approval {status}. {issue_count} issue drafts. Risk level {risk}."
            )
        return NodeResultSummaryResponse(
            node_id=node_id,
            title="Approval gate",
            summary=summary,
            metrics={
                "approval_status": status,
                "issue_count": issue_count,
                "risk_level": risk,
            },
        )
    if node_id == "github_issue_creator":
        created = output.get("created_issues") or []
        skipped = state.status == "skipped"
        created_count = len(created) if isinstance(created, list) else 0
        mode = str(output.get("mode") or "pending")
        if skipped:
            summary = "GitHub issue creation was skipped. No real issues were created."
        elif mode == "mock":
            summary = f"Created {created_count} mock issue results. No real GitHub issues were created."
        else:
            summary = f"Created {created_count} GitHub issues after approval."
        return NodeResultSummaryResponse(
            node_id=node_id,
            title="GitHub issue creation",
            summary=summary,
            metrics={
                "created_issues": created_count,
                "skipped": skipped,
                "mode": output.get("mode"),
            },
        )
    if node_id == "linkedin_draft_generator":
        draft = (
            output.get("linkedin_draft")
            if isinstance(output.get("linkedin_draft"), dict)
            else output
        )
        hashtags = draft.get("hashtags") if isinstance(draft, dict) else []
        return NodeResultSummaryResponse(
            node_id=node_id,
            title="LinkedIn draft generated",
            summary=f"LinkedIn draft generated with {len(hashtags) if isinstance(hashtags, list) else 0} hashtags.",
            metrics={"hashtags": len(hashtags) if isinstance(hashtags, list) else 0},
        )
    if node_id == "markdown_report_writer":
        artifacts = (
            output.get("artifacts") if isinstance(output.get("artifacts"), list) else []
        )
        return NodeResultSummaryResponse(
            node_id=node_id,
            title="Reports written",
            summary=f"Saved {len(artifacts)} markdown artifacts.",
            metrics={"artifacts": len(artifacts)},
        )
    return NodeResultSummaryResponse(
        node_id=node_id,
        title=node_id.replace("_", " ").title(),
        summary=(
            "No output yet" if not output else f"{len(output)} output fields available."
        ),
        metrics={"status": state.status.value},
    )


def _dict_value(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _latest_artifacts_by_type(
    artifacts: list[ArtifactResponse],
) -> dict[str, ArtifactResponse]:
    latest: dict[str, ArtifactResponse] = {}
    for artifact in artifacts:
        current = latest.get(artifact.artifact_type)
        if current is None or artifact.created_at >= current.created_at:
            latest[artifact.artifact_type] = artifact
    return latest


def _guided_steps(
    current_step: str,
    *,
    completed_through: int,
    failed_step: str | None = None,
) -> GuidedStepsResponse:
    steps = []
    for index, (step_id, label, description) in enumerate(GUIDED_STEP_DEFINITIONS):
        if step_id == failed_step:
            status = "failed"
        elif index <= completed_through:
            status = "completed"
        elif step_id == current_step:
            status = "active"
        else:
            status = "pending"
        steps.append(
            GuidedStepResponse(
                id=step_id,
                label=label,
                status=status,
                description=description,
            )
        )
    return GuidedStepsResponse(current_step=current_step, steps=steps)
