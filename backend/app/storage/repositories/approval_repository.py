from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.approval import ApprovalModel
from app.storage.exceptions import ApprovalAlreadyResolvedError, ApprovalNotFoundError
from app.storage.ports import ApprovalRepositoryPort
from app.storage.records import ApprovalRecord


class SQLAlchemyApprovalRepository(ApprovalRepositoryPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def create_approval(self, run_id: str, node_execution_id: str) -> str:
        async with self.session_factory() as session:
            async with session.begin():
                approval = ApprovalModel(
                    run_id=UUID(run_id),
                    node_execution_id=UUID(node_execution_id),
                    status="pending",
                )
                session.add(approval)
            return str(approval.id)

    async def get(self, approval_id: str) -> ApprovalRecord:
        async with self.session_factory() as session:
            approval = await session.get(ApprovalModel, UUID(approval_id))
            if approval is None:
                raise ApprovalNotFoundError(approval_id)
            return _approval_record(approval)

    async def resolve(
        self,
        approval_id: str,
        decision: Literal["approved", "rejected"],
        reason: str | None,
    ) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                approval = (
                    await session.execute(
                        select(ApprovalModel)
                        .where(ApprovalModel.id == UUID(approval_id))
                        .with_for_update()
                    )
                ).scalar_one_or_none()
                if approval is None:
                    raise ApprovalNotFoundError(approval_id)
                if approval.status != "pending":
                    raise ApprovalAlreadyResolvedError(approval_id, approval.status)
                approval.status = decision
                approval.reason = reason
                approval.resolved_at = datetime.now(UTC)


def _approval_record(approval: ApprovalModel) -> ApprovalRecord:
    return ApprovalRecord(
        id=str(approval.id),
        run_id=str(approval.run_id),
        node_execution_id=str(approval.node_execution_id),
        status=approval.status,
        requested_at=approval.requested_at,
        resolved_at=approval.resolved_at,
        resolved_by=str(approval.resolved_by) if approval.resolved_by else None,
        reason=approval.reason,
    )
