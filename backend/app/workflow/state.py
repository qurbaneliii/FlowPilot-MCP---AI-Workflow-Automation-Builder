from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.workflow.graph import WorkflowGraph


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    SKIPPED = "skipped"


class NodeExecutionState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    status: NodeStatus = NodeStatus.PENDING
    output: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RunState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    graph: WorkflowGraph
    node_states: dict[str, NodeExecutionState]
    status: Literal[
        "pending", "running", "completed", "failed", "waiting_for_approval"
    ] = "pending"
    error: dict[str, Any] | None = None


def create_run_state(run_id: str, graph: WorkflowGraph) -> RunState:
    return RunState(
        run_id=run_id,
        graph=graph,
        node_states={
            node.id: NodeExecutionState(node_id=node.id) for node in graph.nodes
        },
    )
