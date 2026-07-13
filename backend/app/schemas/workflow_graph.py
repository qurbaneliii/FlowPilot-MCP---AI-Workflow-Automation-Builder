from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.agents.schemas import ValidatorOutput
from app.workflow.graph import WorkflowGraph
from app.schemas.ui import (
    GuidedStepsResponse,
    NextActionResponse,
    WorkflowReviewResponse,
)


class GenerateWorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1)
    repo_url: str = Field(min_length=1)


class GenerateWorkflowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    workflow: WorkflowGraph
    validation: ValidatorOutput
    summary: "WorkflowSummaryResponse"
    node_display: list["WorkflowNodeDisplayResponse"] = Field(default_factory=list)
    layout: "WorkflowLayoutResponse | None" = None
    warnings: list[str] = Field(default_factory=list)
    guided_steps: GuidedStepsResponse
    next_action: NextActionResponse
    workflow_review: WorkflowReviewResponse


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    workflow: WorkflowGraph
    metadata: dict[str, Any] = Field(default_factory=dict)
    summary: "WorkflowSummaryResponse | None" = None
    node_display: list["WorkflowNodeDisplayResponse"] = Field(default_factory=list)
    layout: "WorkflowLayoutResponse | None" = None
    guided_steps: GuidedStepsResponse | None = None
    next_action: NextActionResponse | None = None
    workflow_review: WorkflowReviewResponse | None = None


class WorkflowSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    repo_url: str | None = None
    node_count: int
    estimated_stages: int
    risky_action_count: int
    approval_required: bool
    mode: str | None = None
    status_label: str


class WorkflowNodeDisplayResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    name: str
    subtitle: str
    icon: str
    order: int
    stage: int
    dependencies: list[str] = Field(default_factory=list)
    risk_level: str = "none"
    approval_required: bool = False
    description: str


class WorkflowLayoutNodeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    x: int
    y: int


class WorkflowLayoutResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: str = "vertical"
    nodes: list[WorkflowLayoutNodeResponse] = Field(default_factory=list)
