from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.storage.mappers import (
    orm_row_to_workflow_graph,
    run_state_from_rows,
    run_state_to_row_updates,
    workflow_graph_to_orm_fields,
)
from app.workflow.graph import NodeDefinition, WorkflowGraph
from app.workflow.state import NodeExecutionState, NodeStatus, RunState


def test_workflow_graph_mapping_round_trip() -> None:
    graph = WorkflowGraph(nodes=[NodeDefinition(id="A", type="noop", name="A")])

    fields = workflow_graph_to_orm_fields(
        graph,
        source_prompt="Audit this repo",
        user_id="00000000-0000-0000-0000-000000000001",
    )
    restored = orm_row_to_workflow_graph(
        SimpleNamespace(graph_json=fields["graph_json"])
    )

    assert restored == graph
    assert fields["source_prompt"] == "Audit this repo"
    assert fields["name"] == "A"


def test_run_state_mapping_from_rows() -> None:
    run_id = uuid4()
    graph = WorkflowGraph(nodes=[NodeDefinition(id="A", type="noop", name="A")])
    run_row = SimpleNamespace(
        id=run_id,
        status="completed",
        version=2,
        error_summary=None,
    )
    completed_at = datetime.now(UTC)
    node_rows = [
        SimpleNamespace(
            node_id="A",
            status="completed",
            output_json={"ok": True},
            input_snapshot_json={"_dependencies": {}},
            error_json=None,
            retry_count=1,
            started_at=completed_at,
            completed_at=completed_at,
        )
    ]

    run_state = run_state_from_rows(run_row, graph, node_rows)

    assert run_state.run_id == str(run_id)
    assert run_state.version == 2
    assert run_state.node_states["A"].input_snapshot == {"_dependencies": {}}
    assert run_state.node_states["A"].output == {"ok": True}


def test_run_state_to_row_updates() -> None:
    completed_at = datetime.now(UTC)
    graph = WorkflowGraph(nodes=[NodeDefinition(id="A", type="noop", name="A")])
    run_state = RunState(
        run_id=str(uuid4()),
        graph=graph,
        status="completed",
        node_states={
            "A": NodeExecutionState(
                node_id="A",
                status=NodeStatus.COMPLETED,
                input_snapshot={"_dependencies": {}},
                output={"ok": True},
                completed_at=completed_at,
            )
        },
    )

    run_update, node_updates = run_state_to_row_updates(run_state)

    assert run_update["status"] == "completed"
    assert run_update["completed_at"] == completed_at
    assert node_updates == [
        {
            "node_id": "A",
            "status": "completed",
            "input_snapshot_json": {"_dependencies": {}},
            "output_json": {"ok": True},
            "error_json": None,
            "started_at": None,
            "completed_at": completed_at,
            "retry_count": 0,
        }
    ]
