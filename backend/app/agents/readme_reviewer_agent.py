from typing import Any, ClassVar

from pydantic import BaseModel

from app.agents.base import AgentPort
from app.agents.backends import AgentBackendPort
from app.agents.runner import AgentRunner
from app.agents.schemas import ReadmeReviewerOutput


class ReadmeReviewerAgent(AgentPort):
    output_schema: ClassVar[type[BaseModel]] = ReadmeReviewerOutput

    def __init__(self, backend: AgentBackendPort | None = None) -> None:
        self.runner = AgentRunner(
            agent_name="readme_reviewer",
            output_schema=ReadmeReviewerOutput,
            backend=backend,
        )
        self.tools: list[object] = []

    async def run(self, input_payload: dict[str, Any]) -> ReadmeReviewerOutput:
        result = await self.runner.run(input_payload)
        return ReadmeReviewerOutput.model_validate(result)
