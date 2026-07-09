from app.core.api_errors import ApiError
from app.schemas.approval import ApprovalDecisionResponse
from app.services.artifact_service import ArtifactService
from app.services.store import STORE, now, new_id
from app.storage.records import ApprovalRecord
from app.workflow.engine import WorkflowEngine
from app.workflow.state import NodeStatus, RunState


class ApprovalService:
    def __init__(self) -> None:
        self.engine = WorkflowEngine(max_attempts=1, base_delay=0)
        self.artifacts = ArtifactService()

    async def ensure_pending_for_run(
        self, run_state: RunState
    ) -> ApprovalRecord | None:
        for node_id, node_state in run_state.node_states.items():
            if node_state.status != NodeStatus.WAITING_FOR_APPROVAL:
                continue
            for approval_id, record in STORE.approvals.items():
                if (
                    record.run_id == run_state.run_id
                    and STORE.approval_nodes.get(approval_id) == node_id
                ):
                    _attach_approval_id(run_state, node_id, approval_id)
                    return record
            approval_id = new_id()
            record = ApprovalRecord(
                id=approval_id,
                run_id=run_state.run_id,
                node_execution_id=node_id,
                status="pending",
                requested_at=now(),
            )
            STORE.approvals[approval_id] = record
            STORE.approval_nodes[approval_id] = node_id
            _attach_approval_id(run_state, node_id, approval_id)
            return record
        return None

    async def approve(
        self, approval_id: str, reason: str | None = None
    ) -> ApprovalDecisionResponse:
        record = _approval_or_404(approval_id)
        if record.status != "pending":
            raise ApiError(
                409,
                "APPROVAL_ALREADY_RESOLVED",
                "Approval has already been resolved.",
                {"status": record.status},
            )
        STORE.approvals[approval_id] = record.model_copy(
            update={"status": "approved", "resolved_at": now(), "reason": reason}
        )
        run_state = STORE.runs[record.run_id]
        node_id = STORE.approval_nodes[approval_id]
        updated = await self.engine.resume(run_state, node_id, "approved")
        STORE.runs[record.run_id] = updated
        await self.artifacts.persist_from_run(updated)
        from app.services.run_query_service import RunQueryService

        return ApprovalDecisionResponse(
            approval_id=approval_id,
            decision="approved",
            run=await RunQueryService().get_run(record.run_id),
        )

    async def reject(
        self, approval_id: str, reason: str | None = None
    ) -> ApprovalDecisionResponse:
        record = _approval_or_404(approval_id)
        if record.status != "pending":
            raise ApiError(
                409,
                "APPROVAL_ALREADY_RESOLVED",
                "Approval has already been resolved.",
                {"status": record.status},
            )
        STORE.approvals[approval_id] = record.model_copy(
            update={"status": "rejected", "resolved_at": now(), "reason": reason}
        )
        run_state = STORE.runs[record.run_id]
        node_id = STORE.approval_nodes[approval_id]
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
        STORE.runs[record.run_id] = updated
        await self.artifacts.persist_from_run(updated)
        from app.services.run_query_service import RunQueryService

        return ApprovalDecisionResponse(
            approval_id=approval_id,
            decision="rejected",
            run=await RunQueryService().get_run(record.run_id),
        )


def _approval_or_404(approval_id: str) -> ApprovalRecord:
    record = STORE.approvals.get(approval_id)
    if record is None:
        raise ApiError(404, "APPROVAL_NOT_FOUND", "Approval not found.")
    return record


def _attach_approval_id(run_state: RunState, node_id: str, approval_id: str) -> None:
    node_state = run_state.node_states[node_id]
    node_state.output = {**(node_state.output or {}), "approval_id": approval_id}
