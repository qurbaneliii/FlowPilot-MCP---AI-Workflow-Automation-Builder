import re

import app.workflow.nodes  # noqa: F401
from app.agents.planner_agent import PlannerAgent
from app.agents.validator_agent import ValidatorAgent
from app.core.api_errors import ApiError
from app.schemas.workflow_graph import (
    GenerateWorkflowRequest,
    GenerateWorkflowResponse,
    WorkflowResponse,
)
from app.services.store import STORE, WorkflowEntry, new_id, now


GITHUB_REPO_RE = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?(?:\.git)?$"
)


class WorkflowGenerationService:
    async def generate(
        self, request: GenerateWorkflowRequest
    ) -> GenerateWorkflowResponse:
        if not GITHUB_REPO_RE.match(request.repo_url):
            raise ApiError(
                422,
                "INVALID_REPO_URL",
                "Repository URL must be a GitHub owner/repo URL.",
                {"repo_url": request.repo_url},
            )
        graph = await PlannerAgent().run(
            {
                "prompt": request.prompt,
                "source_prompt": request.prompt,
                "repo_url": request.repo_url,
            }
        )
        validation = await ValidatorAgent().run(
            {"graph": graph.model_dump(mode="json")}
        )
        if not validation.valid:
            raise ApiError(
                422,
                "WORKFLOW_VALIDATION_FAILED",
                "Generated workflow did not pass validation.",
                {"issues": validation.issues},
            )
        graph_to_save = validation.corrected_graph or graph
        workflow_id = new_id()
        STORE.workflows[workflow_id] = WorkflowEntry(
            id=workflow_id,
            graph=graph_to_save,
            source_prompt=request.prompt,
            repo_url=request.repo_url,
            created_at=now(),
        )
        return GenerateWorkflowResponse(
            workflow_id=workflow_id,
            workflow=graph_to_save,
            validation=validation,
            warnings=validation.issues,
        )

    async def get(self, workflow_id: str) -> WorkflowResponse:
        workflow = STORE.workflows.get(workflow_id)
        if workflow is None:
            raise ApiError(404, "WORKFLOW_NOT_FOUND", "Workflow not found.")
        return WorkflowResponse(
            workflow_id=workflow_id,
            workflow=workflow.graph,
            metadata={
                "source_prompt": workflow.source_prompt,
                "repo_url": workflow.repo_url,
                "created_at": workflow.created_at.isoformat(),
            },
        )
