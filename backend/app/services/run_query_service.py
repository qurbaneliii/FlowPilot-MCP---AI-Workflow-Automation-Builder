from datetime import datetime

from app.core.api_errors import ApiError
from app.schemas.run import (
    NodeRunResponse,
    PendingApprovalResponse,
    RunListResponse,
    RunResponse,
)
from app.services.artifact_service import ArtifactService
from app.services.store import STORE
from app.workflow.state import RunState


class RunQueryService:
    def __init__(self) -> None:
        self.artifacts = ArtifactService()

    async def get_run(self, run_id: str) -> RunResponse:
        run_state = STORE.runs.get(run_id)
        if run_state is None:
            raise ApiError(404, "RUN_NOT_FOUND", "Run not found.")
        return await self._to_response(run_state)

    async def list_runs(self, limit: int = 20, offset: int = 0) -> RunListResponse:
        run_ids = list(STORE.runs.keys())[::-1][offset : offset + limit]
        return RunListResponse(
            runs=[await self._to_response(STORE.runs[run_id]) for run_id in run_ids],
            limit=limit,
            offset=offset,
        )

    async def _to_response(self, run_state: RunState) -> RunResponse:
        artifacts = await self.artifacts.list_for_run(run_state.run_id)
        nodes = [
            NodeRunResponse(
                node_id=node_id,
                status=state.status.value,
                output=state.output,
                error=state.error,
                retry_count=state.retry_count,
                started_at=state.started_at,
                completed_at=state.completed_at,
            )
            for node_id, state in run_state.node_states.items()
        ]
        errors = [
            {"node_id": node_id, **(state.error or {})}
            for node_id, state in run_state.node_states.items()
            if state.error
        ]
        return RunResponse(
            run_id=run_state.run_id,
            workflow_id=STORE.run_workflows.get(run_state.run_id, ""),
            status=run_state.status,
            started_at=_started_at(run_state),
            completed_at=_completed_at(run_state),
            nodes=nodes,
            logs=[],
            node_outputs={
                node_id: state.output
                for node_id, state in run_state.node_states.items()
            },
            errors=errors,
            artifacts=artifacts,
            pending_approval=_pending_approval(run_state),
            mode=_mode(run_state),
        )


def _pending_approval(run_state: RunState) -> PendingApprovalResponse | None:
    for approval_id, record in STORE.approvals.items():
        if record.run_id != run_state.run_id or record.status != "pending":
            continue
        node_id = STORE.approval_nodes[approval_id]
        output = run_state.node_states[node_id].output or {}
        return PendingApprovalResponse(
            approval_id=approval_id,
            status=record.status,
            node_id=node_id,
            approval_summary=output.get("approval_summary"),
            issue_drafts=output.get("issue_drafts", []),
            target_repository=output.get("target_repository"),
            risk_level=output.get("risk_level"),
            downstream_action=output.get("downstream_action"),
            node_to_resume_after_approval=output.get("node_to_resume_after_approval"),
        )
    return None


def _mode(run_state: RunState) -> str | None:
    for state in run_state.node_states.values():
        output = state.output or {}
        mode = output.get("mode") if isinstance(output, dict) else None
        if isinstance(mode, str):
            return mode
        snapshot = output.get("repo_snapshot") if isinstance(output, dict) else None
        if isinstance(snapshot, dict) and isinstance(snapshot.get("mode"), str):
            return snapshot["mode"]
    return None


def _started_at(run_state: RunState) -> datetime | None:
    values = [
        state.started_at for state in run_state.node_states.values() if state.started_at
    ]
    return min(values) if values else None


def _completed_at(run_state: RunState) -> datetime | None:
    if run_state.status not in {"completed", "failed"}:
        return None
    values = [
        state.completed_at
        for state in run_state.node_states.values()
        if state.completed_at
    ]
    return max(values) if values else None
