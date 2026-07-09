from fastapi import APIRouter

from app.schemas.approval import ApprovalDecisionRequest, ApprovalDecisionResponse
from app.services.approval_service import ApprovalService


router = APIRouter()


@router.post(
    "/approvals/{approval_id}/approve", response_model=ApprovalDecisionResponse
)
async def approve(
    approval_id: str, request: ApprovalDecisionRequest | None = None
) -> ApprovalDecisionResponse:
    return await ApprovalService().approve(
        approval_id, reason=request.reason if request else None
    )


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalDecisionResponse)
async def reject(
    approval_id: str, request: ApprovalDecisionRequest | None = None
) -> ApprovalDecisionResponse:
    return await ApprovalService().reject(
        approval_id, reason=request.reason if request else None
    )
