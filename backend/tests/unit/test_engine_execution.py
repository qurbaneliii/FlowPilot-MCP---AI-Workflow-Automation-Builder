import pytest

from app.workflow import node_registry
from app.workflow.engine import WorkflowEngine
from app.workflow.exceptions import InvalidResumeStateError
from app.workflow.graph import NodeDefinition, WorkflowGraph
from app.workflow.state import NodeStatus, create_run_state
from tests.fixtures.fake_node_handlers import (
    AlwaysFailHandler,
    ApprovalStubHandler,
    NoOpSuccessHandler,
)


async def no_sleep(seconds: float) -> None:
    return None


def node(
    node_id: str,
    node_type: str = "noop",
    dependencies: list[str] | None = None,
) -> NodeDefinition:
    return NodeDefinition(
        id=node_id,
        type=node_type,
        name=node_id,
        dependencies=dependencies or [],
    )


@pytest.fixture(autouse=True)
def registered_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(node_registry, "_REGISTRY", {})
    node_registry.register_node("noop")(NoOpSuccessHandler)
    node_registry.register_node("fail")(AlwaysFailHandler)
    node_registry.register_node("approval")(ApprovalStubHandler)


@pytest.mark.asyncio
async def test_full_success_path_all_nodes_complete() -> None:
    graph = WorkflowGraph(nodes=[node("A"), node("B", dependencies=["A"])])
    run_state = create_run_state("run-1", graph)

    result = await WorkflowEngine(sleep=no_sleep).run(run_state)

    assert result.status == "completed"
    assert result.node_states["A"].status == NodeStatus.COMPLETED
    assert result.node_states["B"].status == NodeStatus.COMPLETED


@pytest.mark.asyncio
async def test_failure_cascades_downstream_to_skipped() -> None:
    graph = WorkflowGraph(nodes=[node("A", "fail"), node("B", dependencies=["A"])])
    run_state = create_run_state("run-1", graph)

    result = await WorkflowEngine(sleep=no_sleep).run(run_state)

    assert result.status == "failed"
    assert result.node_states["A"].status == NodeStatus.FAILED
    assert result.node_states["B"].status == NodeStatus.SKIPPED


@pytest.mark.asyncio
async def test_failure_does_not_affect_independent_branch() -> None:
    graph = WorkflowGraph(
        nodes=[
            node("A"),
            node("B", "fail", ["A"]),
            node("C", "noop", ["A"]),
            node("D", "noop", ["B", "C"]),
        ]
    )
    run_state = create_run_state("run-1", graph)

    result = await WorkflowEngine(sleep=no_sleep).run(run_state)

    assert result.status == "failed"
    assert result.node_states["B"].status == NodeStatus.FAILED
    assert result.node_states["C"].status == NodeStatus.COMPLETED
    assert result.node_states["D"].status == NodeStatus.SKIPPED


@pytest.mark.asyncio
async def test_human_approval_pauses_run_and_returns_control() -> None:
    graph = WorkflowGraph(
        nodes=[
            node("A"),
            node("approval", "approval", ["A"]),
            node("B", dependencies=["approval"]),
        ]
    )
    run_state = create_run_state("run-1", graph)

    result = await WorkflowEngine(sleep=no_sleep).run(run_state)

    assert result.status == "waiting_for_approval"
    assert result.node_states["approval"].status == NodeStatus.WAITING_FOR_APPROVAL
    assert result.node_states["B"].status == NodeStatus.PENDING


@pytest.mark.asyncio
async def test_resume_after_approval_continues_remaining_nodes() -> None:
    graph = WorkflowGraph(
        nodes=[node("approval", "approval"), node("B", dependencies=["approval"])]
    )
    engine = WorkflowEngine(sleep=no_sleep)
    run_state = await engine.run(create_run_state("run-1", graph))

    result = await engine.resume(run_state, "approval", "approved")

    assert result.status == "completed"
    assert result.node_states["approval"].status == NodeStatus.COMPLETED
    assert result.node_states["B"].status == NodeStatus.COMPLETED


@pytest.mark.asyncio
async def test_resume_after_rejection_skips_downstream_and_fails_run() -> None:
    graph = WorkflowGraph(
        nodes=[node("approval", "approval"), node("B", dependencies=["approval"])]
    )
    engine = WorkflowEngine(sleep=no_sleep)
    run_state = await engine.run(create_run_state("run-1", graph))

    result = await engine.resume(run_state, "approval", "rejected")

    assert result.status == "failed"
    assert result.error == {
        "code": "rejected_by_user",
        "message": "Workflow rejected by user",
    }
    assert result.node_states["approval"].status == NodeStatus.SKIPPED
    assert result.node_states["B"].status == NodeStatus.SKIPPED


@pytest.mark.asyncio
async def test_resume_on_non_waiting_node_raises_invalid_resume_state() -> None:
    graph = WorkflowGraph(nodes=[node("A")])
    engine = WorkflowEngine(sleep=no_sleep)
    run_state = await engine.run(create_run_state("run-1", graph))

    with pytest.raises(InvalidResumeStateError):
        await engine.resume(run_state, "A", "approved")
