from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from app.storage.records import ApprovalRecord, ArtifactRecord
from app.workflow.graph import WorkflowGraph
from app.workflow.state import RunState


@dataclass
class WorkflowEntry:
    id: str
    graph: WorkflowGraph
    source_prompt: str
    repo_url: str
    created_at: datetime


@dataclass
class InMemoryStore:
    workflows: dict[str, WorkflowEntry] = field(default_factory=dict)
    runs: dict[str, RunState] = field(default_factory=dict)
    run_workflows: dict[str, str] = field(default_factory=dict)
    approvals: dict[str, ApprovalRecord] = field(default_factory=dict)
    approval_nodes: dict[str, str] = field(default_factory=dict)
    artifacts: dict[str, list[ArtifactRecord]] = field(default_factory=dict)

    def reset(self) -> None:
        self.workflows.clear()
        self.runs.clear()
        self.run_workflows.clear()
        self.approvals.clear()
        self.approval_nodes.clear()
        self.artifacts.clear()


STORE = InMemoryStore()


def new_id() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(UTC)
