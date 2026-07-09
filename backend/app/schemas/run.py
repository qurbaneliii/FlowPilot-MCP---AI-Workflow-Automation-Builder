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
    status: str
    output: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    run_id: str
    artifact_type: str
    filename: str
    content: str
    created_at: datetime
    mode: str | None = None
    source_node_id: str | None = None


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
    started_at: datetime | None = None
    completed_at: datetime | None = None
    nodes: list[NodeRunResponse]
    logs: list[dict[str, Any]] = Field(default_factory=list)
    node_outputs: dict[str, dict[str, Any] | None] = Field(default_factory=dict)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[ArtifactResponse] = Field(default_factory=list)
    pending_approval: PendingApprovalResponse | None = None
    mode: str | None = None


class RunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runs: list[RunResponse]
    limit: int
    offset: int
