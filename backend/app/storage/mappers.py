from typing import Any
from uuid import UUID

from app.workflow.graph import WorkflowGraph
from app.workflow.state import NodeExecutionState, RunState


def workflow_graph_to_orm_fields(
    graph: WorkflowGraph, source_prompt: str, user_id: str
) -> dict[str, Any]:
    return {
        "user_id": UUID(user_id),
        "name": _graph_name(graph),
        "source_prompt": source_prompt,
        "graph_json": graph.model_dump(mode="json"),
    }


def orm_row_to_workflow_graph(row: Any) -> WorkflowGraph:
    return WorkflowGraph.model_validate(row.graph_json)


def run_state_from_rows(
    run_row: Any,
    workflow_graph: WorkflowGraph,
    node_execution_rows: list[Any],
) -> RunState:
    return RunState(
        run_id=str(run_row.id),
        graph=workflow_graph,
        node_states={
            row.node_id: NodeExecutionState(
                node_id=row.node_id,
                status=row.status,
                output=row.output_json,
                input_snapshot=row.input_snapshot_json,
                error=row.error_json,
                retry_count=row.retry_count,
                started_at=row.started_at,
                completed_at=row.completed_at,
            )
            for row in node_execution_rows
        },
        status=run_row.status,
        version=run_row.version,
        error=(
            {"code": "run_failed", "message": run_row.error_summary}
            if run_row.error_summary
            else None
        ),
    )


def run_state_to_row_updates(
    run_state: RunState,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    run_update = {
        "status": run_state.status,
        "completed_at": _latest_completed_at(run_state),
        "error_summary": (
            run_state.error.get("message")
            if run_state.error and isinstance(run_state.error.get("message"), str)
            else None
        ),
    }
    node_updates = [
        {
            "node_id": node_state.node_id,
            "status": node_state.status.value,
            "input_snapshot_json": node_state.input_snapshot,
            "output_json": node_state.output,
            "error_json": node_state.error,
            "started_at": node_state.started_at,
            "completed_at": node_state.completed_at,
            "retry_count": node_state.retry_count,
        }
        for node_state in run_state.node_states.values()
    ]
    return run_update, node_updates


def _graph_name(graph: WorkflowGraph) -> str:
    if not graph.nodes:
        return "Empty Workflow"
    return graph.nodes[0].name or "Generated Workflow"


def _latest_completed_at(run_state: RunState) -> Any:
    if run_state.status not in {"completed", "failed"}:
        return None
    completed_values = [
        node_state.completed_at
        for node_state in run_state.node_states.values()
        if node_state.completed_at is not None
    ]
    return max(completed_values) if completed_values else None
