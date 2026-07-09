from typing import Any, ClassVar

from pydantic import BaseModel

from app.agents.base import AgentPort
from app.agents.backends import AgentBackendPort
from app.agents.runner import AgentRunner
from app.agents.schemas import RepoAnalyzerOutput
from app.mcp.registry import get_client


class RepoAnalyzerAgent(AgentPort):
    output_schema: ClassVar[type[BaseModel]] = RepoAnalyzerOutput

    def __init__(self, backend: AgentBackendPort | None = None) -> None:
        self.runner = AgentRunner(
            agent_name="repo_analyzer",
            output_schema=RepoAnalyzerOutput,
            backend=backend,
        )
        self.tools = [
            get_client("github"),
            get_client("filesystem"),
            get_client("openai_mcp"),
        ]

    async def run(self, input_payload: dict[str, Any]) -> RepoAnalyzerOutput:
        result = await self.runner.run(input_payload)
        return RepoAnalyzerOutput.model_validate(result)
