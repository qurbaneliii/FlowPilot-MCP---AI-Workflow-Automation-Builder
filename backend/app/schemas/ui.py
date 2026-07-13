from pydantic import BaseModel, ConfigDict, Field


class GuidedStepResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    status: str
    description: str


class GuidedStepsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_step: str
    steps: list[GuidedStepResponse] = Field(default_factory=list)


class NextActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    primary_label: str | None = None
    secondary_label: str | None = None
    target_tab: str | None = None
    target_node_id: str | None = None
    severity: str = "info"


class ModeExplanationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    label: str
    description: str


class ModeExplanationsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mcp: ModeExplanationResponse
    agent: ModeExplanationResponse
    storage: ModeExplanationResponse


class DemoModeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active: bool
    label: str
    description: str


class WorkflowReviewWriteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    requires_approval: bool
    mode: str


class WorkflowReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    plain_english_summary: str
    reads: list[str] = Field(default_factory=list)
    writes: list[WorkflowReviewWriteResponse] = Field(default_factory=list)
    approval_required: bool
    risk_level: str
    estimated_outputs: list[str] = Field(default_factory=list)


class CompletionIssueCreationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str
    created_count: int
    message: str


class CompletionOutputResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    label: str


class CompletionSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    artifact_count: int
    issue_creation: CompletionIssueCreationResponse
    primary_outputs: list[CompletionOutputResponse] = Field(default_factory=list)
