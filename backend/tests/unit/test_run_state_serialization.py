from app.workflow.graph import NodeDefinition, WorkflowGraph
from app.workflow.state import create_run_state


def test_run_state_json_round_trip_preserves_value() -> None:
    graph = WorkflowGraph(
        nodes=[
            NodeDefinition(id="A", type="noop", name="A"),
            NodeDefinition(id="B", type="noop", name="B", dependencies=["A"]),
        ]
    )
    run_state = create_run_state("run-1", graph)

    serialized = run_state.model_dump_json()
    restored = type(run_state).model_validate_json(serialized)

    assert restored == run_state
