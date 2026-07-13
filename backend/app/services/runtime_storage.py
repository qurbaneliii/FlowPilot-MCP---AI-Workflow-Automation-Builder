from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.models.approval import ApprovalModel
from app.models.node_execution import NodeExecutionModel
from app.models.run import RunModel
from app.models.workflow import WorkflowModel
from app.services.store import STORE, WorkflowEntry, new_id, now
from app.storage.exceptions import RunNotFoundError
from app.storage.records import ApprovalRecord, ArtifactRecord
from app.storage.repositories import (
    SQLAlchemyApprovalRepository,
    SQLAlchemyArtifactRepository,
    SQLAlchemyRunRepository,
    SQLAlchemyWorkflowRepository,
)
from app.workflow.graph import WorkflowGraph
from app.workflow.state import RunState, create_run_state


@dataclass(frozen=True)
class StoredWorkflow:
    id: str
    graph: WorkflowGraph
    source_prompt: str
    repo_url: str
    created_at: datetime


class RuntimeStorage:
    """Single runtime boundary used by API services in memory or Postgres mode."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.mode = self.settings.effective_storage_mode
        if self.mode not in {"memory", "postgres"}:
            raise ValueError("STORAGE_MODE must be 'memory' or 'postgres'.")
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        if self.mode == "postgres":
            if not self.settings.database_url:
                raise ValueError("DATABASE_URL is required when STORAGE_MODE=postgres.")
            engine = create_async_engine(self.settings.database_url, pool_pre_ping=True)
            self.session_factory = async_sessionmaker(engine, expire_on_commit=False)
            self.workflows = SQLAlchemyWorkflowRepository(self.session_factory)
            self.runs = SQLAlchemyRunRepository(self.session_factory)
            self.approvals = SQLAlchemyApprovalRepository(self.session_factory)
            self.artifacts = SQLAlchemyArtifactRepository(self.session_factory)

    @property
    def persistent(self) -> bool:
        return self.mode == "postgres"

    async def create_workflow(
        self, graph: WorkflowGraph, source_prompt: str, repo_url: str
    ) -> str:
        if self.mode == "memory":
            workflow_id = new_id()
            STORE.workflows[workflow_id] = WorkflowEntry(
                id=workflow_id,
                graph=graph,
                source_prompt=source_prompt,
                repo_url=repo_url,
                created_at=now(),
            )
            return workflow_id
        return await self.workflows.create(
            graph, source_prompt, str(self.settings.default_user_id)
        )

    async def get_workflow(self, workflow_id: str) -> StoredWorkflow | None:
        if self.mode == "memory":
            entry = STORE.workflows.get(workflow_id)
            return (
                StoredWorkflow(
                    entry.id,
                    entry.graph,
                    entry.source_prompt,
                    entry.repo_url,
                    entry.created_at,
                )
                if entry
                else None
            )
        assert self.session_factory is not None
        async with self.session_factory() as session:
            row = await session.get(WorkflowModel, UUID(workflow_id))
            if row is None:
                return None
            graph = WorkflowGraph.model_validate(row.graph_json)
            return StoredWorkflow(
                id=str(row.id),
                graph=graph,
                source_prompt=row.source_prompt,
                repo_url=_repo_url_from_graph(graph),
                created_at=row.created_at,
            )

    async def create_run(self, workflow_id: str, graph: WorkflowGraph) -> RunState:
        if self.mode == "memory":
            run_id = new_id()
            run_state = create_run_state(run_id, graph)
            STORE.runs[run_id] = run_state
            STORE.run_workflows[run_id] = workflow_id
            return run_state
        return await self.runs.create_run(
            workflow_id, graph, str(self.settings.default_user_id)
        )

    async def load_run(self, run_id: str) -> RunState | None:
        if self.mode == "memory":
            return STORE.runs.get(run_id)
        try:
            return await self.runs.load_run_state(run_id)
        except RunNotFoundError:
            return None

    async def save_run(self, run_state: RunState, expected_version: int) -> None:
        if self.mode == "memory":
            STORE.runs[run_state.run_id] = run_state
            return
        await self.runs.save_run_state(run_state, expected_version)

    async def workflow_id_for_run(self, run_id: str) -> str:
        if self.mode == "memory":
            return STORE.run_workflows.get(run_id, "")
        assert self.session_factory is not None
        async with self.session_factory() as session:
            workflow_id = await session.scalar(
                select(RunModel.workflow_id).where(RunModel.id == UUID(run_id))
            )
            return str(workflow_id) if workflow_id else ""

    async def list_run_ids(self, limit: int, offset: int) -> list[str]:
        if self.mode == "memory":
            return list(STORE.runs.keys())[::-1][offset : offset + limit]
        assert self.session_factory is not None
        async with self.session_factory() as session:
            rows = await session.scalars(
                select(RunModel.id)
                .order_by(RunModel.started_at.desc(), RunModel.id.desc())
                .offset(offset)
                .limit(limit)
            )
            return [str(run_id) for run_id in rows]

    async def find_or_create_approval(
        self, run_id: str, node_id: str
    ) -> ApprovalRecord:
        if self.mode == "memory":
            for approval_id, record in STORE.approvals.items():
                if (
                    record.run_id == run_id
                    and STORE.approval_nodes.get(approval_id) == node_id
                ):
                    return record
            approval_id = new_id()
            record = ApprovalRecord(
                id=approval_id,
                run_id=run_id,
                node_execution_id=node_id,
                status="pending",
                requested_at=now(),
            )
            STORE.approvals[approval_id] = record
            STORE.approval_nodes[approval_id] = node_id
            return record
        assert self.session_factory is not None
        async with self.session_factory() as session:
            node_execution = (
                await session.execute(
                    select(NodeExecutionModel).where(
                        NodeExecutionModel.run_id == UUID(run_id),
                        NodeExecutionModel.node_id == node_id,
                    )
                )
            ).scalar_one()
            existing = (
                await session.execute(
                    select(ApprovalModel).where(
                        ApprovalModel.run_id == UUID(run_id),
                        ApprovalModel.node_execution_id == node_execution.id,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                return _approval_record(existing, node_id)
        approval_id = await self.approvals.create_approval(
            run_id, str(node_execution.id)
        )
        record = await self.approvals.get(approval_id)
        return record.model_copy(update={"node_execution_id": node_id})

    async def get_approval(self, approval_id: str) -> ApprovalRecord | None:
        if self.mode == "memory":
            return STORE.approvals.get(approval_id)
        assert self.session_factory is not None
        async with self.session_factory() as session:
            row = await session.get(ApprovalModel, UUID(approval_id))
            if row is None:
                return None
            node_id = await session.scalar(
                select(NodeExecutionModel.node_id).where(
                    NodeExecutionModel.id == row.node_execution_id
                )
            )
            return _approval_record(row, str(node_id or ""))

    async def resolve_approval(
        self,
        approval_id: str,
        decision: Literal["approved", "rejected"],
        reason: str | None,
    ) -> ApprovalRecord:
        if self.mode == "memory":
            record = STORE.approvals[approval_id].model_copy(
                update={"status": decision, "resolved_at": now(), "reason": reason}
            )
            STORE.approvals[approval_id] = record
            return record
        await self.approvals.resolve(approval_id, decision, reason)
        record = await self.get_approval(approval_id)
        assert record is not None
        return record

    async def save_artifact(
        self, run_id: str, artifact_type: str, content_markdown: str
    ) -> str:
        if self.mode == "memory":
            raise RuntimeError("Memory artifacts are managed by ArtifactService.")
        return await self.artifacts.save(run_id, artifact_type, content_markdown)

    async def list_artifact_records(self, run_id: str) -> list[ArtifactRecord]:
        if self.mode == "memory":
            return STORE.artifacts.get(run_id, [])
        return await self.artifacts.list_for_run(run_id)


def _repo_url_from_graph(graph: WorkflowGraph) -> str:
    for node in graph.nodes:
        repo_url = node.config.get("repo_url")
        if isinstance(repo_url, str) and repo_url:
            return repo_url
    return ""


def _approval_record(row: ApprovalModel, node_id: str) -> ApprovalRecord:
    return ApprovalRecord(
        id=str(row.id),
        run_id=str(row.run_id),
        node_execution_id=node_id,
        status=row.status,
        requested_at=row.requested_at,
        resolved_at=row.resolved_at,
        resolved_by=str(row.resolved_by) if row.resolved_by else None,
        reason=row.reason,
    )


@lru_cache
def get_runtime_storage() -> RuntimeStorage:
    return RuntimeStorage()


def reset_runtime_storage() -> None:
    get_runtime_storage.cache_clear()
