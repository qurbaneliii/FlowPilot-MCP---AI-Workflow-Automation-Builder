from typing import ClassVar

from pydantic import BaseModel

from app.agents.linkedin_draft_agent import LinkedInDraftAgent
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
    dependency_outputs,
    failed,
    log_node,
    run_controlled,
)


@register_node("linkedin_draft_generator")
class LinkedInDraftGeneratorHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        if context.inputs.get("publish") is True:
            return failed(
                "publish_not_allowed",
                "LinkedIn node only generates draft text and never publishes.",
            )

        async def generate() -> dict:
            result = await LinkedInDraftAgent().run(
                {
                    "artifacts": [],
                    "context": dependency_outputs(context),
                    "publish": False,
                }
            )
            return result.model_dump(mode="json")

        result = await run_controlled(
            context,
            generate,
            failure_code="linkedin_draft_generator_failed",
            failure_message="LinkedIn draft generation failed in a controlled way.",
        )
        if isinstance(result, NodeExecutionResult):
            return result
        log_node(
            context,
            "linkedin_draft_generator_completed",
            text_length=len(result.get("post_text", "")),
        )
        return completed(
            {
                "linkedin_draft": result,
                "post_text": result.get("post_text"),
                "published": False,
            }
        )
