import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from uuid import UUID

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import exc, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.node_execution import NodeExecutionModel
from app.storage.exceptions import (
    ApprovalAlreadyResolvedError,
    ConcurrentModificationError,
)
from app.storage.repositories import (
    SQLAlchemyApprovalRepository,
    SQLAlchemyArtifactRepository,
    SQLAlchemyRunRepository,
    SQLAlchemyWorkflowRepository,
)
from app.workflow import node_registry
from app.workflow.engine import WorkflowEngine
from app.workflow.graph import NodeDefinition, WorkflowGraph
from app.workflow.state import NodeStatus
from tests.fixtures.fake_node_handlers import (
    ApprovalStubHandler,
    DependencyAssertingHandler,
    NoOpSuccessHandler,
    ValueProducerHandler,
)


async def no_sleep(seconds: float) -> None:
    return None


def graph_with(*nodes: NodeDefinition) -> WorkflowGraph:
    return WorkflowGraph(nodes=list(nodes))


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


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip(
            "No TEST_DATABASE_URL or DATABASE_URL configured for Postgres tests"
        )
    engine = create_async_engine(url)
    try:
        asyncio.run(_probe_database(engine))
    except Exception as exc_info:
        pytest.skip(f"Postgres is not reachable: {exc_info}")
    finally:
        asyncio.run(engine.dispose())
    old_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    _run_alembic_upgrade()
    yield url
    if old_database_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = old_database_url


async def _probe_database(engine) -> None:
    async with engine.connect() as connection:
        await connection.execute(text("select 1"))


def _run_alembic_upgrade() -> None:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(config, "head")


@pytest_asyncio.fixture
async def session_factory(
    postgres_url: str,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(postgres_url, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE TABLE artifacts, approvals, node_executions, runs, workflows "
                "RESTART IDENTITY CASCADE"
            )
        )
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture(autouse=True)
def registered_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(node_registry, "_REGISTRY", {})
    node_registry.register_node("noop")(NoOpSuccessHandler)
    node_registry.register_node("approval")(ApprovalStubHandler)
    node_registry.register_node("value_producer")(ValueProducerHandler)
    node_registry.register_node("dependency_asserting")(DependencyAssertingHandler)


@pytest_asyncio.fixture
async def repositories(
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[
    SQLAlchemyWorkflowRepository,
    SQLAlchemyRunRepository,
    SQLAlchemyApprovalRepository,
    SQLAlchemyArtifactRepository,
]:
    return (
        SQLAlchemyWorkflowRepository(session_factory),
        SQLAlchemyRunRepository(session_factory),
        SQLAlchemyApprovalRepository(session_factory),
        SQLAlchemyArtifactRepository(session_factory),
    )


USER_ID = "00000000-0000-0000-0000-000000000001"


async def create_workflow_and_run(
    workflow_repo: SQLAlchemyWorkflowRepository,
    run_repo: SQLAlchemyRunRepository,
    graph: WorkflowGraph,
) -> tuple[str, str]:
    workflow_id = await workflow_repo.create(graph, "Audit repo", USER_ID)
    run_state = await run_repo.create_run(workflow_id, graph, USER_ID)
    return workflow_id, run_state.run_id


@pytest.mark.asyncio
async def test_create_and_load_workflow_roundtrip(repositories) -> None:
    workflow_repo, _, _, _ = repositories
    graph = graph_with(node("A"))

    workflow_id = await workflow_repo.create(graph, "Audit repo", USER_ID)
    loaded = await workflow_repo.get(workflow_id)

    assert loaded == graph


@pytest.mark.asyncio
async def test_create_run_initializes_all_node_execution_rows_pending(
    repositories,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    workflow_repo, run_repo, _, _ = repositories
    graph = graph_with(node("A"), node("B", dependencies=["A"]))
    workflow_id = await workflow_repo.create(graph, "Audit repo", USER_ID)

    run_state = await run_repo.create_run(workflow_id, graph, USER_ID)

    assert all(
        state.status == NodeStatus.PENDING for state in run_state.node_states.values()
    )
    async with session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(NodeExecutionModel).order_by(NodeExecutionModel.node_id)
                )
            )
            .scalars()
            .all()
        )
    assert [(row.node_id, row.status) for row in rows] == [
        ("A", "pending"),
        ("B", "pending"),
    ]


@pytest.mark.asyncio
async def test_save_and_reload_run_state_roundtrip(repositories) -> None:
    workflow_repo, run_repo, _, _ = repositories
    graph = graph_with(
        node("A", "value_producer"), node("B", "dependency_asserting", ["A"])
    )
    workflow_id = await workflow_repo.create(graph, "Audit repo", USER_ID)
    run_state = await run_repo.create_run(workflow_id, graph, USER_ID)
    result = await WorkflowEngine(sleep=no_sleep).run(run_state)

    await run_repo.save_run_state(result, expected_version=1)
    reloaded = await run_repo.load_run_state(result.run_id)

    assert reloaded == result


@pytest.mark.asyncio
async def test_optimistic_concurrency_conflict_on_stale_save(repositories) -> None:
    workflow_repo, run_repo, _, _ = repositories
    graph = graph_with(node("A"))
    workflow_id, run_id = await create_workflow_and_run(workflow_repo, run_repo, graph)
    first = await run_repo.load_run_state(run_id)
    second = await run_repo.load_run_state(run_id)
    first_result = await WorkflowEngine(sleep=no_sleep).run(first)

    await run_repo.save_run_state(first_result, expected_version=first.version)

    second_result = await WorkflowEngine(sleep=no_sleep).run(second)
    with pytest.raises(ConcurrentModificationError):
        await run_repo.save_run_state(second_result, expected_version=second.version)
    assert UUID(workflow_id)


@pytest.mark.asyncio
async def test_approval_double_resolve_race_only_one_succeeds(
    repositories,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    workflow_repo, run_repo, approval_repo, _ = repositories
    graph = graph_with(node("approval", "approval"))
    _, run_id = await create_workflow_and_run(workflow_repo, run_repo, graph)
    async with session_factory() as session:
        node_execution_id = (
            await session.execute(select(NodeExecutionModel.id))
        ).scalar_one()
    approval_id = await approval_repo.create_approval(run_id, str(node_execution_id))

    results = await asyncio.gather(
        approval_repo.resolve(approval_id, "approved", "first"),
        approval_repo.resolve(approval_id, "rejected", "second"),
        return_exceptions=True,
    )

    successes = [result for result in results if result is None]
    failures = [result for result in results if isinstance(result, Exception)]
    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], ApprovalAlreadyResolvedError)
    record = await approval_repo.get(approval_id)
    assert record.status in {"approved", "rejected"}
    assert record.reason in {"first", "second"}


@pytest.mark.asyncio
async def test_approval_reject_persists_cascaded_skips_correctly(repositories) -> None:
    workflow_repo, run_repo, _, _ = repositories
    graph = graph_with(
        node("approval", "approval"), node("B", dependencies=["approval"])
    )
    workflow_id = await workflow_repo.create(graph, "Audit repo", USER_ID)
    run_state = await run_repo.create_run(workflow_id, graph, USER_ID)
    engine = WorkflowEngine(sleep=no_sleep)
    paused = await engine.run(run_state)
    await run_repo.save_run_state(paused, expected_version=1)

    reloaded = await run_repo.load_run_state(paused.run_id)
    rejected = await engine.resume(reloaded, "approval", "rejected")
    await run_repo.save_run_state(rejected, expected_version=reloaded.version)
    final = await run_repo.load_run_state(paused.run_id)

    assert final.status == "failed"
    assert final.node_states["approval"].status == NodeStatus.SKIPPED
    assert final.node_states["B"].status == NodeStatus.SKIPPED


@pytest.mark.asyncio
async def test_artifact_save_and_list_for_run(repositories) -> None:
    workflow_repo, run_repo, _, artifact_repo = repositories
    graph = graph_with(node("A"))
    _, run_id = await create_workflow_and_run(workflow_repo, run_repo, graph)

    artifact_id = await artifact_repo.save(run_id, "repo_audit_report", "# Report")
    artifacts = await artifact_repo.list_for_run(run_id)

    assert len(artifacts) == 1
    assert artifacts[0].id == artifact_id
    assert artifacts[0].content_markdown == "# Report"


@pytest.mark.asyncio
async def test_unique_constraint_prevents_duplicate_node_execution_row(
    repositories,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    workflow_repo, run_repo, _, _ = repositories
    graph = graph_with(node("A"))
    _, run_id = await create_workflow_and_run(workflow_repo, run_repo, graph)

    async with session_factory() as session:
        async with session.begin():
            session.add(
                NodeExecutionModel(
                    run_id=UUID(run_id),
                    node_id="A",
                    node_type="noop",
                    status="pending",
                    logs=[],
                )
            )
            with pytest.raises(exc.IntegrityError):
                await session.flush()


def test_migration_upgrade_head_idempotent(postgres_url: str) -> None:
    os.environ["DATABASE_URL"] = postgres_url
    _run_alembic_upgrade()
    _run_alembic_upgrade()


@pytest.mark.asyncio
async def test_full_engine_run_persisted_end_to_end(repositories) -> None:
    workflow_repo, run_repo, _, _ = repositories
    graph = graph_with(
        node("A"),
        node("approval", "approval", ["A"]),
        node("B", dependencies=["approval"]),
    )
    workflow_id = await workflow_repo.create(graph, "Audit repo", USER_ID)
    run_state = await run_repo.create_run(workflow_id, graph, USER_ID)
    engine = WorkflowEngine(sleep=no_sleep)

    paused = await engine.run(run_state)
    assert paused.status == "waiting_for_approval"
    await run_repo.save_run_state(paused, expected_version=1)

    reloaded_after_restart = await run_repo.load_run_state(paused.run_id)
    resumed = await engine.resume(reloaded_after_restart, "approval", "approved")
    await run_repo.save_run_state(
        resumed, expected_version=reloaded_after_restart.version
    )
    final = await run_repo.load_run_state(paused.run_id)

    assert final.status == "completed"
    assert final.node_states["A"].status == NodeStatus.COMPLETED
    assert final.node_states["approval"].status == NodeStatus.COMPLETED
    assert final.node_states["B"].status == NodeStatus.COMPLETED
