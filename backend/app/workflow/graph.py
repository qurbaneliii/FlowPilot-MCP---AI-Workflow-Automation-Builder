from collections import Counter
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.workflow.exceptions import (
    DanglingDependencyError,
    DuplicateNodeIdError,
    GraphCycleError,
)


class NodeDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    name: str
    config: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)


class WorkflowGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[NodeDefinition]


def validate_and_sort(graph: WorkflowGraph) -> list[str]:
    """Validate a graph and return node ids in deterministic topological order.

    When multiple nodes are eligible at the same time, ties are broken by the
    insertion order in ``WorkflowGraph.nodes``. This keeps repeated runs stable
    without relying on dictionary or set traversal order.
    """

    _raise_for_duplicate_ids(graph)
    node_ids = {node.id for node in graph.nodes}
    _raise_for_dangling_dependencies(graph, node_ids)
    _raise_for_cycles(graph)
    return _topological_sort_by_insertion_order(graph)


def _raise_for_duplicate_ids(graph: WorkflowGraph) -> None:
    counts = Counter(node.id for node in graph.nodes)
    for node_id, count in counts.items():
        if count > 1:
            raise DuplicateNodeIdError(node_id=node_id)


def _raise_for_dangling_dependencies(graph: WorkflowGraph, node_ids: set[str]) -> None:
    for node in graph.nodes:
        for dependency in node.dependencies:
            if dependency not in node_ids:
                raise DanglingDependencyError(
                    node_id=node.id, missing_dependency=dependency
                )


def _raise_for_cycles(graph: WorkflowGraph) -> None:
    dependencies_by_node = {node.id: node.dependencies for node in graph.nodes}
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node_id: str) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            cycle_start = stack.index(node_id)
            raise GraphCycleError(cycle_path=stack[cycle_start:] + [node_id])

        visiting.add(node_id)
        stack.append(node_id)
        for dependency in dependencies_by_node[node_id]:
            visit(dependency)
        stack.pop()
        visiting.remove(node_id)
        visited.add(node_id)

    for node in graph.nodes:
        visit(node.id)


def _topological_sort_by_insertion_order(graph: WorkflowGraph) -> list[str]:
    resolved: set[str] = set()
    remaining = {node.id for node in graph.nodes}
    ordered: list[str] = []

    while remaining:
        eligible = [
            node
            for node in graph.nodes
            if node.id in remaining
            and all(dependency in resolved for dependency in node.dependencies)
        ]
        if not eligible:
            _raise_for_cycles(graph)
        for node in eligible:
            ordered.append(node.id)
            resolved.add(node.id)
            remaining.remove(node.id)

    return ordered
