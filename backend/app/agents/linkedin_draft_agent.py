from typing import Any, ClassVar

from pydantic import BaseModel

from app.agents.base import AgentPort
from app.agents.backends import AgentBackendPort
from app.agents.runner import AgentRunner
from app.agents.schemas import LinkedInDraftOutput


class LinkedInDraftAgent(AgentPort):
    output_schema: ClassVar[type[BaseModel]] = LinkedInDraftOutput

    def __init__(self, backend: AgentBackendPort | None = None) -> None:
        self.runner = AgentRunner(
            agent_name="linkedin_draft",
            output_schema=LinkedInDraftOutput,
            backend=backend,
        )
        self.tools: list[object] = []

    async def run(self, input_payload: dict[str, Any]) -> LinkedInDraftOutput:
        result = await self.runner.run(input_payload)
        return LinkedInDraftOutput.model_validate(result)
