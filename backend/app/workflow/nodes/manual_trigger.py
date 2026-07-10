from typing import ClassVar

from pydantic import BaseModel

from app.workflow.node_registry import register_node
from app.workflow.nodes.base import (
    NodeExecutionContext,
    NodeExecutionResult,
    NodeHandler,
)
from app.workflow.nodes.common import (
    EmptyInput,
    EmptyOutput,
    completed,
    log_node,
    utc_now_iso,
)


class ManualTriggerOutput(EmptyOutput):
    triggered_at: str
    source_prompt: str
    repo_url: str


@register_node("manual_trigger")
class ManualTriggerHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = ManualTriggerOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        source_prompt = str(
            context.inputs.get("source_prompt")
            or context.inputs.get("prompt")
            or "Analyze this GitHub repository and generate issue drafts."
        )
        repo_url = str(context.inputs.get("repo_url") or "")
        log_node(context, "manual_trigger_completed", has_repo_url=bool(repo_url))
        return completed(
            {
                "triggered_at": utc_now_iso(),
                "source_prompt": source_prompt,
                "repo_url": repo_url,
            }
        )
