from typing import Any

from app.workflow.graph import NodeDefinition
from app.workflow.state import RunState


def resolve_node_inputs(node: NodeDefinition, run_state: RunState) -> dict[str, Any]:
    """Build the effective input payload for a node about to execute.

    Static config is copied first and has precedence over auto-derived keys.
    Dependency outputs are attached under the reserved ``_dependencies`` key
    unless the author explicitly supplied that key in node config.
    """

    resolved: dict[str, Any] = dict(node.config)
    dependency_outputs = {
        dependency_id: run_state.node_states[dependency_id].output
        for dependency_id in node.dependencies
    }
    resolved.setdefault("_dependencies", dependency_outputs)
    return resolved
