from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RunModel(Base):
    __tablename__ = "runs"
    __table_args__ = (
        Index("ix_runs_workflow_id", "workflow_id"),
        Index("ix_runs_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False)
    version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)

    workflow = relationship("WorkflowModel", back_populates="runs")
    node_executions = relationship(
        "NodeExecutionModel", back_populates="run", cascade="all, delete"
    )
    approvals = relationship(
        "ApprovalModel", back_populates="run", cascade="all, delete"
    )
    artifacts = relationship(
        "ArtifactModel", back_populates="run", cascade="all, delete"
    )
