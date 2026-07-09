from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WorkflowModel(Base):
    __tablename__ = "workflows"
    __table_args__ = (Index("ix_workflows_user_id", "user_id"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str | None] = mapped_column(Text(), nullable=True)
    source_prompt: Mapped[str] = mapped_column(Text(), nullable=False)
    graph_json: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    runs = relationship("RunModel", back_populates="workflow", cascade="all, delete")
