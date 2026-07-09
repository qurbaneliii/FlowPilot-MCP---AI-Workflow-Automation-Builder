import asyncio
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from app.workflow.exceptions import PermanentError, TransientError
from app.workflow.nodes.base import (
    NodeExecutionContext,
    NodeExecutionResult,
    NodeHandler,
)


class EmptyInput(BaseModel):
    pass


class EmptyOutput(BaseModel):
    value: dict[str, Any] = Field(default_factory=dict)


class NoOpSuccessHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        return NodeExecutionResult(
            status="completed",
            output={"ok": True, "node_id": context.node.id},
        )


class AlwaysFailHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        return NodeExecutionResult(
            status="failed",
            error={"code": "always_failed", "message": "Always fails"},
        )


class FlakyHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        self.calls += 1
        failures_before_success = int(
            context.node.config.get("failures_before_success", 1)
        )
        if self.calls <= failures_before_success:
            raise TransientError(f"transient failure {self.calls}")
        return NodeExecutionResult(
            status="completed",
            output={"attempts": self.calls},
        )


class AlwaysTransientHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput
    calls: ClassVar[int] = 0

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        type(self).calls += 1
        raise TransientError("still failing")


class PermanentErrorHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput
    calls: ClassVar[int] = 0

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        type(self).calls += 1
        raise PermanentError("permanent failure")


class SlowHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        await asyncio.sleep(float(context.node.config.get("sleep_seconds", 1.0)))
        return NodeExecutionResult(status="completed", output={"slow": False})


class ApprovalStubHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        return NodeExecutionResult(
            status="waiting_for_approval",
            output={"pending": True},
        )
