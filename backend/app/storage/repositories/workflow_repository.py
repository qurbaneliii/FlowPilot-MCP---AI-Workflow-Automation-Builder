from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.workflow import WorkflowModel
from app.storage.mappers import orm_row_to_workflow_graph, workflow_graph_to_orm_fields
from app.storage.ports import WorkflowRepositoryPort
from app.workflow.graph import WorkflowGraph


class SQLAlchemyWorkflowRepository(WorkflowRepositoryPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def create(
        self, graph: WorkflowGraph, source_prompt: str, user_id: str
    ) -> str:
        async with self.session_factory() as session:
            async with session.begin():
                workflow = WorkflowModel(
                    **workflow_graph_to_orm_fields(graph, source_prompt, user_id)
                )
                session.add(workflow)
            return str(workflow.id)

    async def get(self, workflow_id: str) -> WorkflowGraph | None:
        async with self.session_factory() as session:
            workflow = await session.get(WorkflowModel, UUID(workflow_id))
            if workflow is None:
                return None
            return orm_row_to_workflow_graph(workflow)
