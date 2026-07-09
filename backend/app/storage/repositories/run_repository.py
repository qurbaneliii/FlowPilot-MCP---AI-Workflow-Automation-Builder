from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.node_execution import NodeExecutionModel
from app.models.run import RunModel
from app.models.workflow import WorkflowModel
from app.storage.exceptions import (
    ConcurrentModificationError,
    RunNotFoundError,
    WorkflowNotFoundError,
)
from app.storage.mappers import (
    orm_row_to_workflow_graph,
    run_state_from_rows,
    run_state_to_row_updates,
)
from app.storage.ports import RunRepositoryPort
from app.workflow.graph import WorkflowGraph
from app.workflow.state import RunState, create_run_state


class SQLAlchemyRunRepository(RunRepositoryPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def create_run(
        self, workflow_id: str, graph: WorkflowGraph, user_id: str
    ) -> RunState:
        async with self.session_factory() as session:
            async with session.begin():
                workflow = await session.get(WorkflowModel, UUID(workflow_id))
                if workflow is None:
                    raise WorkflowNotFoundError(workflow_id)

                run = RunModel(
                    workflow_id=UUID(workflow_id),
                    user_id=UUID(user_id),
                    status="pending",
                    version=1,
                )
                session.add(run)
                await session.flush()
                for node in graph.nodes:
                    session.add(
                        NodeExecutionModel(
                            run_id=run.id,
                            node_id=node.id,
                            node_type=node.type,
                            status="pending",
                            logs=[],
                        )
                    )
            run_state = create_run_state(str(run.id), graph)
            run_state.version = run.version
            return run_state

    async def load_run_state(self, run_id: str) -> RunState:
        async with self.session_factory() as session:
            run = await session.get(RunModel, UUID(run_id))
            if run is None:
                raise RunNotFoundError(run_id)
            workflow = await session.get(WorkflowModel, run.workflow_id)
            if workflow is None:
                raise WorkflowNotFoundError(str(run.workflow_id))
            node_rows = (
                (
                    await session.execute(
                        select(NodeExecutionModel)
                        .where(NodeExecutionModel.run_id == run.id)
                        .order_by(NodeExecutionModel.node_id)
                    )
                )
                .scalars()
                .all()
            )
            return run_state_from_rows(
                run,
                orm_row_to_workflow_graph(workflow),
                list(node_rows),
            )

    async def save_run_state(self, run_state: RunState, expected_version: int) -> int:
        async with self.session_factory() as session:
            async with session.begin():
                run = (
                    await session.execute(
                        select(RunModel)
                        .where(RunModel.id == UUID(run_state.run_id))
                        .with_for_update()
                    )
                ).scalar_one_or_none()
                if run is None:
                    raise RunNotFoundError(run_state.run_id)
                if run.version != expected_version:
                    raise ConcurrentModificationError(
                        run_state.run_id,
                        expected_version=expected_version,
                        actual_version=run.version,
                    )

                run_update, node_updates = run_state_to_row_updates(run_state)
                for key, value in run_update.items():
                    setattr(run, key, value)
                run.version += 1

                node_rows = {
                    row.node_id: row
                    for row in (
                        await session.execute(
                            select(NodeExecutionModel).where(
                                NodeExecutionModel.run_id == run.id
                            )
                        )
                    ).scalars()
                }
                node_by_id = {node.id: node for node in run_state.graph.nodes}
                for node_update in node_updates:
                    node_id = node_update["node_id"]
                    row = node_rows.get(node_id)
                    if row is None:
                        row = NodeExecutionModel(
                            run_id=run.id,
                            node_id=node_id,
                            node_type=node_by_id[node_id].type,
                            status=node_update["status"],
                            logs=[],
                        )
                        session.add(row)
                    for key, value in node_update.items():
                        if key != "node_id":
                            setattr(row, key, value)
                new_version = run.version
            run_state.version = new_version
            return new_version
