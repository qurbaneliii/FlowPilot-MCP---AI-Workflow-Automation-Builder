from typing import Any, ClassVar

from pydantic import BaseModel

from app.agents.base import AgentPort
from app.agents.backends import AgentBackendPort
from app.agents.runner import AgentRunner
from app.agents.schemas import ExecutorOutput
from app.mcp.registry import get_client


class ExecutorAgent(AgentPort):
    output_schema: ClassVar[type[BaseModel]] = ExecutorOutput

    def __init__(self, backend: AgentBackendPort | None = None) -> None:
        self.runner = AgentRunner(
            agent_name="executor",
            output_schema=ExecutorOutput,
            backend=backend,
        )
        self.tools = [get_client("openai_mcp")]

    async def run(self, input_payload: dict[str, Any]) -> ExecutorOutput:
        result = await self.runner.run(input_payload)
        return ExecutorOutput.model_validate(result)
