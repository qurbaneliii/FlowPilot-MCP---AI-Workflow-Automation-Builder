import pytest

from app.workflow.exceptions import (
    DanglingDependencyError,
    DuplicateNodeIdError,
    GraphCycleError,
)
from app.workflow.graph import NodeDefinition, WorkflowGraph, validate_and_sort


def node(node_id: str, dependencies: list[str] | None = None) -> NodeDefinition:
    return NodeDefinition(
        id=node_id,
        type="noop",
        name=node_id,
        dependencies=dependencies or [],
    )


def test_topological_sort_linear_chain() -> None:
    graph = WorkflowGraph(nodes=[node("A"), node("B", ["A"]), node("C", ["B"])])

    assert validate_and_sort(graph) == ["A", "B", "C"]


def test_topological_sort_diamond_dependency() -> None:
    graph = WorkflowGraph(
        nodes=[
            node("A"),
            node("B", ["A"]),
            node("C", ["A"]),
            node("D", ["B", "C"]),
        ]
    )

    assert validate_and_sort(graph) == ["A", "B", "C", "D"]


def test_topological_sort_disconnected_subgraphs() -> None:
    graph = WorkflowGraph(
        nodes=[node("A"), node("B", ["A"]), node("C"), node("D", ["C"])]
    )

    assert validate_and_sort(graph) == ["A", "C", "B", "D"]


def test_topological_sort_deterministic_tie_break() -> None:
    graph = WorkflowGraph(
        nodes=[node("A"), node("B", ["A"]), node("C"), node("D", ["C"])]
    )

    first_order = validate_and_sort(graph)
    for _ in range(100):
        assert validate_and_sort(graph) == first_order


def test_cycle_detection_simple_two_node_cycle() -> None:
    graph = WorkflowGraph(nodes=[node("A", ["B"]), node("B", ["A"])])

    with pytest.raises(GraphCycleError):
        validate_and_sort(graph)


def test_cycle_detection_self_loop() -> None:
    graph = WorkflowGraph(nodes=[node("A", ["A"])])

    with pytest.raises(GraphCycleError) as exc_info:
        validate_and_sort(graph)

    assert exc_info.value.cycle_path == ["A", "A"]


def test_cycle_detection_long_indirect_cycle() -> None:
    graph = WorkflowGraph(nodes=[node("A", ["B"]), node("B", ["C"]), node("C", ["A"])])

    with pytest.raises(GraphCycleError):
        validate_and_sort(graph)


def test_cycle_error_reports_correct_path() -> None:
    graph = WorkflowGraph(nodes=[node("A", ["B"]), node("B", ["C"]), node("C", ["A"])])

    with pytest.raises(GraphCycleError) as exc_info:
        validate_and_sort(graph)

    assert exc_info.value.cycle_path == ["A", "B", "C", "A"]


def test_dangling_dependency_reference_raises() -> None:
    graph = WorkflowGraph(nodes=[node("A", ["missing"])])

    with pytest.raises(DanglingDependencyError) as exc_info:
        validate_and_sort(graph)

    assert exc_info.value.node_id == "A"
    assert exc_info.value.missing_dependency == "missing"


def test_duplicate_node_id_raises() -> None:
    graph = WorkflowGraph(nodes=[node("A"), node("A")])

    with pytest.raises(DuplicateNodeIdError) as exc_info:
        validate_and_sort(graph)

    assert exc_info.value.node_id == "A"


def test_empty_graph_returns_empty_order() -> None:
    assert validate_and_sort(WorkflowGraph(nodes=[])) == []


def test_single_node_no_dependencies() -> None:
    assert validate_and_sort(WorkflowGraph(nodes=[node("A")])) == ["A"]
