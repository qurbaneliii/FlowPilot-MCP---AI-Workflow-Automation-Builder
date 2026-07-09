import pytest

from app.workflow.engine import WorkflowEngine
from app.workflow.exceptions import InvalidStateTransitionError
from app.workflow.state import NodeExecutionState, NodeStatus


def test_valid_transition_pending_to_running() -> None:
    engine = WorkflowEngine()
    state = NodeExecutionState(node_id="A")

    engine._transition(state, NodeStatus.RUNNING)

    assert state.status == NodeStatus.RUNNING


def test_invalid_transition_completed_to_running_raises() -> None:
    engine = WorkflowEngine()
    state = NodeExecutionState(node_id="A", status=NodeStatus.COMPLETED)

    with pytest.raises(InvalidStateTransitionError):
        engine._transition(state, NodeStatus.RUNNING)


@pytest.mark.parametrize(
    "terminal_status",
    [NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.SKIPPED],
)
def test_all_terminal_statuses_reject_further_transitions(
    terminal_status: NodeStatus,
) -> None:
    engine = WorkflowEngine()
    state = NodeExecutionState(node_id="A", status=terminal_status)

    with pytest.raises(InvalidStateTransitionError):
        engine._transition(state, NodeStatus.RUNNING)
