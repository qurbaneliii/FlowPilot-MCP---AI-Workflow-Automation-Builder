from abc import ABC, abstractmethod
from typing import Literal

from app.storage.records import ApprovalRecord, ArtifactRecord
from app.workflow.graph import WorkflowGraph
from app.workflow.state import RunState


class WorkflowRepositoryPort(ABC):
    @abstractmethod
    async def create(
        self, graph: WorkflowGraph, source_prompt: str, user_id: str
    ) -> str: ...

    @abstractmethod
    async def get(self, workflow_id: str) -> WorkflowGraph | None: ...


class RunRepositoryPort(ABC):
    @abstractmethod
    async def create_run(
        self, workflow_id: str, graph: WorkflowGraph, user_id: str
    ) -> RunState: ...

    @abstractmethod
    async def load_run_state(self, run_id: str) -> RunState: ...

    @abstractmethod
    async def save_run_state(self, run_state: RunState, expected_version: int) -> int:
        """Return new version or raise ConcurrentModificationError."""


class ApprovalRepositoryPort(ABC):
    @abstractmethod
    async def create_approval(self, run_id: str, node_execution_id: str) -> str: ...

    @abstractmethod
    async def get(self, approval_id: str) -> ApprovalRecord: ...

    @abstractmethod
    async def resolve(
        self,
        approval_id: str,
        decision: Literal["approved", "rejected"],
        reason: str | None,
    ) -> None:
        """Resolve under row-level lock or raise ApprovalAlreadyResolvedError."""


class ArtifactRepositoryPort(ABC):
    @abstractmethod
    async def save(
        self, run_id: str, artifact_type: str, content_markdown: str
    ) -> str: ...

    @abstractmethod
    async def list_for_run(self, run_id: str) -> list[ArtifactRecord]: ...
