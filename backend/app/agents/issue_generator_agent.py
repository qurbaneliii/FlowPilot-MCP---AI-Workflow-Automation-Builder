from typing import Any, ClassVar

from pydantic import BaseModel

from app.agents.base import AgentPort
from app.agents.backends import AgentBackendPort
from app.agents.runner import AgentRunner
from app.agents.schemas import IssueGeneratorOutput


class IssueGeneratorAgent(AgentPort):
    output_schema: ClassVar[type[BaseModel]] = IssueGeneratorOutput

    def __init__(self, backend: AgentBackendPort | None = None) -> None:
        self.runner = AgentRunner(
            agent_name="issue_generator",
            output_schema=IssueGeneratorOutput,
            backend=backend,
        )
        self.tools: list[object] = []

    async def run(self, input_payload: dict[str, Any]) -> IssueGeneratorOutput:
        result = await self.runner.run(input_payload)
        return IssueGeneratorOutput.model_validate(result)
