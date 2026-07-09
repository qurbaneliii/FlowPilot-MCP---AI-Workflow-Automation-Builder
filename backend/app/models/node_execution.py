from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NodeExecutionModel(Base):
    __tablename__ = "node_executions"
    __table_args__ = (
        UniqueConstraint("run_id", "node_id", name="uq_node_executions_run_node"),
        Index("ix_node_executions_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_id: Mapped[str] = mapped_column(Text(), nullable=False)
    node_type: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False)
    input_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(), nullable=True
    )
    output_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB(), nullable=True)
    logs: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB(), nullable=False, default=list
    )
    error_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB(), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retry_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)

    run = relationship("RunModel", back_populates="node_executions")
    approvals = relationship(
        "ApprovalModel", back_populates="node_execution", cascade="all, delete"
    )
