from typing import Any, ClassVar

from pydantic import BaseModel

from app.agents.base import AgentPort
from app.agents.backends import AgentBackendPort
from app.agents.runner import AgentRunner
from app.workflow.graph import WorkflowGraph
from app.workflow.node_registry import registered_node_types


class PlannerAgent(AgentPort):
    output_schema: ClassVar[type[BaseModel]] = WorkflowGraph

    def __init__(self, backend: AgentBackendPort | None = None) -> None:
        self.runner = AgentRunner(
            agent_name="planner",
            output_schema=WorkflowGraph,
            backend=backend,
        )

    async def run(self, input_payload: dict[str, Any]) -> WorkflowGraph:
        payload = {
            **input_payload,
            "available_node_types": input_payload.get(
                "available_node_types", registered_node_types()
            ),
            "mvp_use_case": "github_repo_audit",
        }
        result = await self.runner.run(payload)
        return WorkflowGraph.model_validate(result)
