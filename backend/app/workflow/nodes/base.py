from abc import ABC, abstractmethod
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict

from app.workflow.graph import NodeDefinition
from app.workflow.state import RunState


class NodeExecutionContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=False)

    node: NodeDefinition
    run_state: RunState


class NodeExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["completed", "failed", "waiting_for_approval"]
    output: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class NodeHandler(ABC):
    input_schema: ClassVar[type[BaseModel]]
    output_schema: ClassVar[type[BaseModel]]

    @abstractmethod
    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        """Execute a node against immutable infrastructure-free run context."""
