from pydantic import BaseModel, ConfigDict

from app.schemas.run import RunResponse


class ApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = None


class ApprovalDecisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    status: str
    decision: str
    run_id: str
    message: str
    run_status: str
    next_poll_recommended: bool
    run: RunResponse
