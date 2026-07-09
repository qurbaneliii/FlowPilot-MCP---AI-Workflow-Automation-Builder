from typing import Any, ClassVar

from pydantic import BaseModel

from app.agents.base import AgentPort
from app.agents.backends import AgentBackendPort
from app.agents.runner import AgentRunner
from app.agents.schemas import ValidatorOutput
from app.workflow.exceptions import GraphValidationError
from app.workflow.graph import NodeDefinition, WorkflowGraph, validate_and_sort


RISKY_WRITE_TYPES = {"github_issue_creator"}
APPROVAL_TYPE = "human_approval"


class ValidatorAgent(AgentPort):
    output_schema: ClassVar[type[BaseModel]] = ValidatorOutput

    def __init__(self, backend: AgentBackendPort | None = None) -> None:
        self.runner = AgentRunner(
            agent_name="validator",
            output_schema=ValidatorOutput,
            backend=backend,
        )

    async def run(self, input_payload: dict[str, Any]) -> ValidatorOutput:
        graph = WorkflowGraph.model_validate(input_payload["graph"])
        try:
            validate_and_sort(graph)
        except GraphValidationError as exc:
            return ValidatorOutput(valid=False, issues=[str(exc)], corrected_graph=None)

        corrected = self._insert_missing_approvals(graph)
        if corrected != graph:
            return ValidatorOutput(
                valid=True,
                issues=["Inserted missing human approval before external write node."],
                corrected_graph=corrected,
            )
        result = await self.runner.run({**input_payload, "graph": graph.model_dump()})
        return ValidatorOutput.model_validate(result)

    def _insert_missing_approvals(self, graph: WorkflowGraph) -> WorkflowGraph:
        nodes = [node.model_copy(deep=True) for node in graph.nodes]
        by_id = {node.id: node for node in nodes}
        changed = False
        for node in list(nodes):
            if node.type not in RISKY_WRITE_TYPES:
                continue
            if any(
                by_id[dependency].type == APPROVAL_TYPE
                for dependency in node.dependencies
            ):
                continue
            approval_id = f"{node.id}_approval"
            approval = NodeDefinition(
                id=approval_id,
                type=APPROVAL_TYPE,
                name=f"Approve {node.name}",
                config={"summary": f"Approval required before {node.name}"},
                dependencies=list(node.dependencies),
            )
            node.dependencies = [approval_id]
            nodes.insert(nodes.index(node), approval)
            by_id[approval_id] = approval
            changed = True
        return WorkflowGraph(nodes=nodes) if changed else graph
