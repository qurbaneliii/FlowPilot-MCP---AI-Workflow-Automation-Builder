from app.workflow.graph import NodeDefinition, WorkflowGraph
from app.workflow.input_resolution import resolve_node_inputs
from app.workflow.state import NodeStatus, create_run_state


def test_resolve_inputs_merges_config_and_dependency_outputs() -> None:
    graph = WorkflowGraph(
        nodes=[
            NodeDefinition(id="A", type="noop", name="A"),
            NodeDefinition(
                id="B",
                type="noop",
                name="B",
                config={"repo": "qurbaneliii/example"},
                dependencies=["A"],
            ),
        ]
    )
    run_state = create_run_state("run-1", graph)
    run_state.node_states["A"].status = NodeStatus.COMPLETED
    run_state.node_states["A"].output = {"value": 42}

    resolved = resolve_node_inputs(graph.nodes[1], run_state)

    assert resolved == {
        "repo": "qurbaneliii/example",
        "_dependencies": {"A": {"value": 42}},
    }


def test_resolve_inputs_config_takes_precedence_on_key_collision() -> None:
    graph = WorkflowGraph(
        nodes=[
            NodeDefinition(id="A", type="noop", name="A"),
            NodeDefinition(
                id="B",
                type="noop",
                name="B",
                config={"_dependencies": {"author": "intent"}},
                dependencies=["A"],
            ),
        ]
    )
    run_state = create_run_state("run-1", graph)
    run_state.node_states["A"].output = {"value": 42}

    resolved = resolve_node_inputs(graph.nodes[1], run_state)

    assert resolved["_dependencies"] == {"author": "intent"}


def test_resolve_inputs_handles_dependency_with_none_output() -> None:
    graph = WorkflowGraph(
        nodes=[
            NodeDefinition(id="A", type="noop", name="A"),
            NodeDefinition(id="B", type="noop", name="B", dependencies=["A"]),
        ]
    )
    run_state = create_run_state("run-1", graph)
    run_state.node_states["A"].status = NodeStatus.COMPLETED
    run_state.node_states["A"].output = None

    resolved = resolve_node_inputs(graph.nodes[1], run_state)

    assert resolved["_dependencies"] == {"A": None}


def test_resolve_inputs_no_dependencies_returns_config_only() -> None:
    graph = WorkflowGraph(
        nodes=[
            NodeDefinition(
                id="A",
                type="noop",
                name="A",
                config={"repo": "qurbaneliii/example"},
            )
        ]
    )
    run_state = create_run_state("run-1", graph)

    resolved = resolve_node_inputs(graph.nodes[0], run_state)

    assert resolved == {"repo": "qurbaneliii/example", "_dependencies": {}}
