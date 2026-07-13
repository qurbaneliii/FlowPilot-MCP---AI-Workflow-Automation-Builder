from __future__ import annotations

from app.core.api_errors import ApiError
from app.schemas.run import RunWorkflowResponse
from app.services.approval_service import ApprovalService
from app.services.artifact_service import ArtifactService
from app.services.runtime_storage import RuntimeStorage, get_runtime_storage
from app.workflow.engine import WorkflowEngine
from app.workflow.state import NodeStatus


class WorkflowRunService:
    def __init__(self, storage: RuntimeStorage | None = None) -> None:
        self.storage = storage or get_runtime_storage()
        self.engine = WorkflowEngine(max_attempts=1, base_delay=0)
        self.approvals = ApprovalService(self.storage)
        self.artifacts = ArtifactService(self.storage)

    async def start(self, workflow_id: str) -> RunWorkflowResponse:
        workflow = await self.storage.get_workflow(workflow_id)
        if workflow is None:
            raise ApiError(404, "WORKFLOW_NOT_FOUND", "Workflow not found.")
        run_state = await self.storage.create_run(workflow_id, workflow.graph)
        return RunWorkflowResponse(run_id=run_state.run_id, status="running")

    async def execute_run(self, run_id: str) -> None:
        run_state = await self.storage.load_run(run_id)
        if run_state is None:
            raise ApiError(404, "RUN_NOT_FOUND", "Run not found.")
        expected_version = run_state.version
        updated = await self.engine.run(run_state)
        await self.storage.save_run(updated, expected_version)
        if updated.status == "waiting_for_approval":
            await self.approvals.ensure_pending_for_run(updated)
        if updated.status in {"completed", "failed"}:
            await self.artifacts.persist_from_run(updated)

    async def skip_issue_creator_after_rejection(
        self, run_id: str, approval_node_id: str
    ) -> None:
        run_state = await self.storage.load_run(run_id)
        if run_state is None:
            raise ApiError(404, "RUN_NOT_FOUND", "Run not found.")
        expected_version = run_state.version
        for node in run_state.graph.nodes:
            if (
                node.type == "github_issue_creator"
                and approval_node_id in node.dependencies
            ):
                state = run_state.node_states[node.id]
                if state.status == NodeStatus.PENDING:
                    state.status = NodeStatus.SKIPPED
                    state.error = {
                        "code": "approval_rejected",
                        "message": "Issue creation skipped after approval rejection.",
                    }
        await self.storage.save_run(run_state, expected_version)
