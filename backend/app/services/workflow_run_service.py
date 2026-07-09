from __future__ import annotations

from app.core.api_errors import ApiError
from app.schemas.run import RunWorkflowResponse
from app.services.approval_service import ApprovalService
from app.services.artifact_service import ArtifactService
from app.services.store import STORE, new_id
from app.workflow.engine import WorkflowEngine
from app.workflow.state import NodeStatus, create_run_state


class WorkflowRunService:
    def __init__(self) -> None:
        self.engine = WorkflowEngine(max_attempts=1, base_delay=0)
        self.approvals = ApprovalService()
        self.artifacts = ArtifactService()

    async def start(self, workflow_id: str) -> RunWorkflowResponse:
        workflow = STORE.workflows.get(workflow_id)
        if workflow is None:
            raise ApiError(404, "WORKFLOW_NOT_FOUND", "Workflow not found.")
        run_id = new_id()
        run_state = create_run_state(run_id, workflow.graph)
        STORE.runs[run_id] = run_state
        STORE.run_workflows[run_id] = workflow_id
        return RunWorkflowResponse(run_id=run_id, status="running")

    async def execute_run(self, run_id: str) -> None:
        run_state = STORE.runs.get(run_id)
        if run_state is None:
            raise ApiError(404, "RUN_NOT_FOUND", "Run not found.")
        updated = await self.engine.run(run_state)
        STORE.runs[run_id] = updated
        if updated.status == "waiting_for_approval":
            await self.approvals.ensure_pending_for_run(updated)
        if updated.status in {"completed", "failed"}:
            await self.artifacts.persist_from_run(updated)

    async def skip_issue_creator_after_rejection(
        self, run_id: str, approval_node_id: str
    ) -> None:
        run_state = STORE.runs[run_id]
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
