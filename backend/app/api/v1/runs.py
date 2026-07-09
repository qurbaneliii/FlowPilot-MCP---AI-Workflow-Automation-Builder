from fastapi import APIRouter, BackgroundTasks, Query

from app.schemas.run import (
    RunListResponse,
    RunResponse,
    RunWorkflowRequest,
    RunWorkflowResponse,
)
from app.services.run_query_service import RunQueryService
from app.services.workflow_run_service import WorkflowRunService


router = APIRouter()


@router.post("/workflows/run", response_model=RunWorkflowResponse)
async def run_workflow(
    request: RunWorkflowRequest, background_tasks: BackgroundTasks
) -> RunWorkflowResponse:
    service = WorkflowRunService()
    response = await service.start(request.workflow_id)
    background_tasks.add_task(service.execute_run, response.run_id)
    return response


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str) -> RunResponse:
    return await RunQueryService().get_run(run_id)


@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> RunListResponse:
    return await RunQueryService().list_runs(limit=limit, offset=offset)
