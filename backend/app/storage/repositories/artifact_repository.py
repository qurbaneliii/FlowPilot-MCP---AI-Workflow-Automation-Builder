from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.artifact import ArtifactModel
from app.storage.ports import ArtifactRepositoryPort
from app.storage.records import ArtifactRecord


class SQLAlchemyArtifactRepository(ArtifactRepositoryPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def save(self, run_id: str, artifact_type: str, content_markdown: str) -> str:
        async with self.session_factory() as session:
            async with session.begin():
                artifact = ArtifactModel(
                    run_id=UUID(run_id),
                    type=artifact_type,
                    content_markdown=content_markdown,
                )
                session.add(artifact)
            return str(artifact.id)

    async def list_for_run(self, run_id: str) -> list[ArtifactRecord]:
        async with self.session_factory() as session:
            rows = (
                (
                    await session.execute(
                        select(ArtifactModel)
                        .where(ArtifactModel.run_id == UUID(run_id))
                        .order_by(ArtifactModel.created_at, ArtifactModel.id)
                    )
                )
                .scalars()
                .all()
            )
            return [
                ArtifactRecord(
                    id=str(row.id),
                    run_id=str(row.run_id),
                    type=row.type,
                    content_markdown=row.content_markdown,
                    created_at=row.created_at,
                )
                for row in rows
            ]
