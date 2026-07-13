from datetime import datetime

from app.core.api_errors import ApiError
from app.schemas.run import RunListResponse, RunResponse
from app.services.artifact_service import ArtifactService
from app.services.run_view_service import RunViewService, infer_mode
from app.services.runtime_storage import RuntimeStorage, get_runtime_storage
from app.services.ui_metadata import demo_mode, mode_explanations
from app.workflow.state import RunState


class RunQueryService:
    def __init__(self, storage: RuntimeStorage | None = None) -> None:
        self.storage = storage or get_runtime_storage()
        self.artifacts = ArtifactService(self.storage)
        self.view = RunViewService()

    async def get_run(self, run_id: str) -> RunResponse:
        run_state = await self.storage.load_run(run_id)
        if run_state is None:
            raise ApiError(404, "RUN_NOT_FOUND", "Run not found.")
        return await self._to_response(run_state)

    async def list_runs(self, limit: int = 20, offset: int = 0) -> RunListResponse:
        run_ids = await self.storage.list_run_ids(limit, offset)
        return RunListResponse(
            runs=[
                await self._to_response(await self._required_run(run_id))
                for run_id in run_ids
            ],
            limit=limit,
            offset=offset,
        )

    async def _to_response(self, run_state: RunState) -> RunResponse:
        artifacts = await self.artifacts.list_for_run(run_state.run_id)
        mode = infer_mode(run_state)
        nodes = self.view.nodes(run_state)
        pending_approval = self.view.pending_approval(run_state)
        approval = self.view.approval_panel(pending_approval, mode=mode)
        errors = [
            {"node_id": node_id, **(state.error or {})}
            for node_id, state in run_state.node_states.items()
            if state.error
        ]
        started_at = _started_at(run_state)
        completed_at = _completed_at(run_state)
        summary = self.view.run_summary(
            run_state,
            artifacts=artifacts,
            mode=mode,
            started_at=started_at,
            completed_at=completed_at,
        )
        return RunResponse(
            run_id=run_state.run_id,
            workflow_id=await self.storage.workflow_id_for_run(run_state.run_id),
            status=run_state.status,
            summary=summary,
            started_at=started_at,
            completed_at=completed_at,
            nodes=nodes,
            timeline=self.view.timeline(run_state),
            approval=approval,
            logs=[],
            node_outputs={
                node_id: state.output
                for node_id, state in run_state.node_states.items()
            },
            node_results=self.view.node_results(run_state),
            errors=errors,
            artifacts=artifacts,
            artifact_tabs=self.view.artifact_tabs(artifacts),
            pending_approval=pending_approval,
            ui_state=self.view.ui_state(run_state, summary=summary, approval=approval),
            inspector=self.view.inspector(run_state),
            layout=self.view.layout(run_state.graph).model_dump(mode="json"),
            mode=mode,
            guided_steps=self.view.guided_steps(run_state),
            next_action=self.view.next_action(run_state),
            mode_explanations=mode_explanations(),
            demo_mode=demo_mode(),
            completion_summary=self.view.completion_summary(run_state, artifacts),
        )

    async def _required_run(self, run_id: str) -> RunState:
        run_state = await self.storage.load_run(run_id)
        if run_state is None:
            raise ApiError(404, "RUN_NOT_FOUND", "Run not found.")
        return run_state


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
