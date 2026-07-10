from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RunWorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str


class RunWorkflowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: str


class NodeRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    id: str | None = None
    type: str | None = None
    name: str | None = None
    subtitle: str | None = None
    status: str
    order: int | None = None
    stage: int | None = None
    dependencies: list[str] = Field(default_factory=list)
    output: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    display: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] | None = None


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    run_id: str
    artifact_type: str
    type: str
    filename: str
    title: str | None = None
    content: str
    created_at: datetime
    mode: str | None = None
    source_node_id: str | None = None
    display: dict[str, Any] = Field(default_factory=dict)


class PendingApprovalResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    approval_id: str
    status: str
    node_id: str
    approval_summary: str | None = None
    issue_drafts: list[dict[str, Any]] = Field(default_factory=list)
    target_repository: str | None = None
    risk_level: str | None = None
    downstream_action: str | None = None
    node_to_resume_after_approval: str | None = None


class RunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    workflow_id: str
    status: str
    summary: "RunSummaryResponse"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    nodes: list[NodeRunResponse]
    timeline: list["RunTimelineEntryResponse"] = Field(default_factory=list)
    approval: "ApprovalPanelResponse | None" = None
    logs: list[dict[str, Any]] = Field(default_factory=list)
    node_outputs: dict[str, dict[str, Any] | None] = Field(default_factory=dict)
    node_results: list["NodeResultSummaryResponse"] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[ArtifactResponse] = Field(default_factory=list)
    artifact_tabs: dict[str, "ArtifactTabResponse"] = Field(default_factory=dict)
    pending_approval: PendingApprovalResponse | None = None
    ui_state: "RunUiStateResponse"
    inspector: dict[str, Any] = Field(default_factory=dict)
    layout: dict[str, Any] | None = None
    mode: str | None = None


class RunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runs: list[RunResponse]
    limit: int
    offset: int


class RunSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    repo_url: str | None = None
    mode: str | None = None
    nodes_total: int
    nodes_completed: int
    nodes_failed: int
    nodes_skipped: int
    nodes_waiting: int
    artifacts_count: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    active_node_id: str | None = None
    next_required_action: str | None = None


class RunTimelineEntryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    name: str
    status: str
    timestamp: datetime | None = None
    message: str
    severity: str = "info"


class ApprovalIssuePreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    priority: str | None = None
    labels: list[str] = Field(default_factory=list)
    body_preview: str


class ApprovalPanelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    status: str
    title: str
    description: str
    target_action: str | None = None
    target_repository: str | None = None
    mode: str | None = None
    risk_level: str | None = None
    issue_count: int = 0
    issue_previews: list[ApprovalIssuePreviewResponse] = Field(default_factory=list)
    issue_drafts: list[dict[str, Any]] = Field(default_factory=list)
    can_approve: bool = True
    can_reject: bool = True


class ArtifactTabResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    available: bool
    artifact_id: str | None = None


class NodeResultSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    title: str
    summary: str
    metrics: dict[str, Any] = Field(default_factory=dict)


class RunUiBannerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    title: str
    message: str


class RunUiStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_view: str
    recommended_tab: str
    canvas_focus_node_id: str | None = None
    show_approval_panel: bool = False
    show_reports_panel: bool = False
    show_completion_summary: bool = False
    banner: RunUiBannerResponse | None = None
