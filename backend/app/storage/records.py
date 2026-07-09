from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ApprovalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    run_id: str
    node_execution_id: str
    status: Literal["pending", "approved", "rejected"]
    requested_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    reason: str | None = None


class ArtifactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    run_id: str
    type: str
    content_markdown: str
    created_at: datetime
