import re

import app.workflow.nodes  # noqa: F401
from app.agents.planner_agent import PlannerAgent
from app.agents.validator_agent import ValidatorAgent
from app.core.api_errors import ApiError
from app.core.config import get_settings
from app.schemas.workflow_graph import (
    GenerateWorkflowRequest,
    GenerateWorkflowResponse,
    WorkflowResponse,
)
from app.services.run_view_service import RunViewService
from app.services.runtime_storage import RuntimeStorage, get_runtime_storage


GITHUB_REPO_RE = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?(?:\.git)?$"
)


class WorkflowGenerationService:
    def __init__(self, storage: RuntimeStorage | None = None) -> None:
        self.view = RunViewService()
        self.storage = storage or get_runtime_storage()

    async def generate(
        self, request: GenerateWorkflowRequest
    ) -> GenerateWorkflowResponse:
        if not GITHUB_REPO_RE.match(request.repo_url):
            raise ApiError(
                422,
                "INVALID_REPO_URL",
                "Enter a valid GitHub repository URL.",
                {
                    "repo_url": request.repo_url,
                    "example": "https://github.com/openai/openai-python",
                },
                severity="warning",
                retryable=False,
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
        workflow_id = await self.storage.create_workflow(
            graph_to_save, request.prompt, request.repo_url
        )
        return GenerateWorkflowResponse(
            workflow_id=workflow_id,
            workflow=graph_to_save,
            validation=validation,
            summary=self.view.workflow_summary(
                graph_to_save,
                repo_url=request.repo_url,
                mode=get_settings().github_mcp_mode,
            ),
            node_display=self.view.node_display(graph_to_save),
            layout=self.view.layout(graph_to_save),
            warnings=validation.issues,
            guided_steps=self.view.generated_guided_steps(),
            next_action=self.view.generated_next_action(),
            workflow_review=self.view.workflow_review(graph_to_save),
        )

    async def get(self, workflow_id: str) -> WorkflowResponse:
        workflow = await self.storage.get_workflow(workflow_id)
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
            summary=self.view.workflow_summary(
                workflow.graph,
                repo_url=workflow.repo_url,
                mode=get_settings().github_mcp_mode,
            ),
            node_display=self.view.node_display(workflow.graph),
            layout=self.view.layout(workflow.graph),
            guided_steps=self.view.generated_guided_steps(),
            next_action=self.view.generated_next_action(),
            workflow_review=self.view.workflow_review(workflow.graph),
        )
