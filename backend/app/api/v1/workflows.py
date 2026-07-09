from fastapi import APIRouter

from app.schemas.workflow_graph import (
    GenerateWorkflowRequest,
    GenerateWorkflowResponse,
    WorkflowResponse,
)
from app.services.workflow_generation_service import WorkflowGenerationService


router = APIRouter()


@router.post("/workflows/generate", response_model=GenerateWorkflowResponse)
async def generate_workflow(
    request: GenerateWorkflowRequest,
) -> GenerateWorkflowResponse:
    return await WorkflowGenerationService().generate(request)


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str) -> WorkflowResponse:
    return await WorkflowGenerationService().get(workflow_id)
