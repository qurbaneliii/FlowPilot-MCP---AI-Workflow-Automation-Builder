from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.agents.schemas import ValidatorOutput
from app.workflow.graph import WorkflowGraph


class GenerateWorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1)
    repo_url: str = Field(min_length=1)


class GenerateWorkflowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    workflow: WorkflowGraph
    validation: ValidatorOutput
    warnings: list[str] = Field(default_factory=list)


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    workflow: WorkflowGraph
    metadata: dict[str, Any] = Field(default_factory=dict)
