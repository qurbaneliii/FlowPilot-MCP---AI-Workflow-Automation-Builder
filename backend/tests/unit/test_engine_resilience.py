import pytest

from app.workflow import node_registry
from app.workflow.engine import WorkflowEngine
from app.workflow.graph import NodeDefinition, WorkflowGraph
from app.workflow.state import NodeStatus, create_run_state
from tests.fixtures.fake_node_handlers import (
    AlwaysTransientHandler,
    FlakyHandler,
    PermanentErrorHandler,
    SlowHandler,
)


async def no_sleep(seconds: float) -> None:
    return None


def node(
    node_id: str,
    node_type: str,
    config: dict[str, object] | None = None,
) -> NodeDefinition:
    return NodeDefinition(
        id=node_id,
        type=node_type,
        name=node_id,
        config=config or {},
    )


@pytest.fixture(autouse=True)
def registered_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(node_registry, "_REGISTRY", {})
    AlwaysTransientHandler.calls = 0
    PermanentErrorHandler.calls = 0
    node_registry.register_node("flaky")(FlakyHandler)
    node_registry.register_node("transient")(AlwaysTransientHandler)
    node_registry.register_node("permanent")(PermanentErrorHandler)
    node_registry.register_node("slow")(SlowHandler)


@pytest.mark.asyncio
async def test_flaky_handler_succeeds_after_retries() -> None:
    graph = WorkflowGraph(nodes=[node("A", "flaky", {"failures_before_success": 2})])
    run_state = create_run_state("run-1", graph)

    result = await WorkflowEngine(
        max_attempts=3, base_delay=0, timeout_seconds=1, sleep=no_sleep
    ).run(run_state)

    assert result.status == "completed"
    assert result.node_states["A"].status == NodeStatus.COMPLETED
    assert result.node_states["A"].retry_count == 2
    assert result.node_states["A"].output == {"attempts": 3}


@pytest.mark.asyncio
async def test_retry_exhausted_after_max_attempts_marks_node_failed() -> None:
    graph = WorkflowGraph(nodes=[node("A", "transient")])
    run_state = create_run_state("run-1", graph)

    result = await WorkflowEngine(
        max_attempts=3, base_delay=0, timeout_seconds=1, sleep=no_sleep
    ).run(run_state)

    assert result.status == "failed"
    assert result.node_states["A"].status == NodeStatus.FAILED
    assert result.node_states["A"].retry_count == 2
    assert result.node_states["A"].error["code"] == "retry_exhausted"
    assert AlwaysTransientHandler.calls == 3


@pytest.mark.asyncio
async def test_permanent_error_does_not_retry() -> None:
    graph = WorkflowGraph(nodes=[node("A", "permanent")])
    run_state = create_run_state("run-1", graph)

    result = await WorkflowEngine(
        max_attempts=3, base_delay=0, timeout_seconds=1, sleep=no_sleep
    ).run(run_state)

    assert result.status == "failed"
    assert result.node_states["A"].status == NodeStatus.FAILED
    assert result.node_states["A"].retry_count == 0
    assert result.node_states["A"].error["code"] == "permanent_error"
    assert PermanentErrorHandler.calls == 1


@pytest.mark.asyncio
async def test_slow_handler_times_out() -> None:
    graph = WorkflowGraph(nodes=[node("A", "slow", {"sleep_seconds": 1.0})])
    run_state = create_run_state("run-1", graph)

    result = await WorkflowEngine(
        max_attempts=1, base_delay=0, timeout_seconds=0.01, sleep=no_sleep
    ).run(run_state)

    assert result.status == "failed"
    assert result.node_states["A"].status == NodeStatus.FAILED
    assert result.node_states["A"].error["code"] == "retry_exhausted"


@pytest.mark.asyncio
async def test_timeout_retried_and_eventually_fails_run() -> None:
    graph = WorkflowGraph(nodes=[node("A", "slow", {"sleep_seconds": 1.0})])
    run_state = create_run_state("run-1", graph)

    result = await WorkflowEngine(
        max_attempts=3, base_delay=0, timeout_seconds=0.01, sleep=no_sleep
    ).run(run_state)

    assert result.status == "failed"
    assert result.node_states["A"].status == NodeStatus.FAILED
    assert result.node_states["A"].retry_count == 2
    assert result.node_states["A"].error["code"] == "retry_exhausted"
