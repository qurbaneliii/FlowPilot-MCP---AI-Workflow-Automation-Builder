from app.core.api_errors import ApiError
from app.schemas.approval import ApprovalDecisionResponse
from app.services.artifact_service import ArtifactService
from app.services.runtime_storage import RuntimeStorage, get_runtime_storage
from app.storage.records import ApprovalRecord
from app.workflow.engine import WorkflowEngine
from app.workflow.state import NodeStatus, RunState


class ApprovalService:
    def __init__(self, storage: RuntimeStorage | None = None) -> None:
        self.storage = storage or get_runtime_storage()
        self.engine = WorkflowEngine(max_attempts=1, base_delay=0)
        self.artifacts = ArtifactService(self.storage)

    async def ensure_pending_for_run(
        self, run_state: RunState
    ) -> ApprovalRecord | None:
        for node_id, node_state in run_state.node_states.items():
            if node_state.status != NodeStatus.WAITING_FOR_APPROVAL:
                continue
            record = await self.storage.find_or_create_approval(
                run_state.run_id, node_id
            )
            expected_version = run_state.version
            _attach_approval_id(run_state, node_id, record.id)
            await self.storage.save_run(run_state, expected_version)
            return record
        return None

    async def approve(
        self, approval_id: str, reason: str | None = None
    ) -> ApprovalDecisionResponse:
        record = await self._approval_or_404(approval_id)
        if record.status != "pending":
            raise ApiError(
                409,
                "APPROVAL_ALREADY_RESOLVED",
                "Approval has already been resolved.",
                {"status": record.status},
            )
        record = await self.storage.resolve_approval(approval_id, "approved", reason)
        run_state = await self.storage.load_run(record.run_id)
        if run_state is None:
            raise ApiError(404, "RUN_NOT_FOUND", "Run not found.")
        node_id = record.node_execution_id
        expected_version = run_state.version
        updated = await self.engine.resume(run_state, node_id, "approved")
        await self.storage.save_run(updated, expected_version)
        await self.artifacts.persist_from_run(updated)
        from app.services.run_query_service import RunQueryService

        run = await RunQueryService(self.storage).get_run(record.run_id)
        return ApprovalDecisionResponse(
            approval_id=approval_id,
            status="approved",
            decision="approved",
            run_id=record.run_id,
            message="Approval recorded. Workflow will resume.",
            run_status=run.status,
            next_poll_recommended=True,
            run=run,
        )

    async def reject(
        self, approval_id: str, reason: str | None = None
    ) -> ApprovalDecisionResponse:
        record = await self._approval_or_404(approval_id)
        if record.status != "pending":
            raise ApiError(
                409,
                "APPROVAL_ALREADY_RESOLVED",
                "Approval has already been resolved.",
                {"status": record.status},
            )
        record = await self.storage.resolve_approval(approval_id, "rejected", reason)
        run_state = await self.storage.load_run(record.run_id)
        if run_state is None:
            raise ApiError(404, "RUN_NOT_FOUND", "Run not found.")
        node_id = record.node_execution_id
        expected_version = run_state.version
        node_state = run_state.node_states[node_id]
        existing = dict(node_state.output or {})
        node_state.status = NodeStatus.COMPLETED
        node_state.output = {**existing, "decision": "rejected"}
        for node in run_state.graph.nodes:
            if node.type == "github_issue_creator" and node_id in node.dependencies:
                issue_state = run_state.node_states[node.id]
                if issue_state.status == NodeStatus.PENDING:
                    issue_state.status = NodeStatus.SKIPPED
                    issue_state.error = {
                        "code": "approval_rejected",
                        "message": "Issue creation skipped after approval rejection.",
                    }
        updated = await self.engine.run(run_state)
        await self.storage.save_run(updated, expected_version)
        await self.artifacts.persist_from_run(updated)
        from app.services.run_query_service import RunQueryService

        run = await RunQueryService(self.storage).get_run(record.run_id)
        return ApprovalDecisionResponse(
            approval_id=approval_id,
            status="rejected",
            decision="rejected",
            run_id=record.run_id,
            message="Approval rejected. GitHub issue creation will be skipped.",
            run_status=run.status,
            next_poll_recommended=True,
            run=run,
        )

    async def _approval_or_404(self, approval_id: str) -> ApprovalRecord:
        record = await self.storage.get_approval(approval_id)
        if record is None:
            raise ApiError(404, "APPROVAL_NOT_FOUND", "Approval not found.")
        return record


def _attach_approval_id(run_state: RunState, node_id: str, approval_id: str) -> None:
    node_state = run_state.node_states[node_id]
    node_state.output = {**(node_state.output or {}), "approval_id": approval_id}
