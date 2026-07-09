import json
import logging
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

from app.mcp.clients.base_http import JSONRPCMCPClient
from app.mcp.ports import ClientMode, ToolCallResult, ToolClientPort, ToolSpec


logger = logging.getLogger(__name__)


class RepoSnapshot(BaseModel):
    model_config = ConfigDict(extra="allow")

    repo_url: str
    metadata: dict[str, Any]
    file_tree: list[str]
    readme: str | None = None
    env_example_present: bool = False
    workflows: list[str] = []


class GitHubMCPClient(JSONRPCMCPClient, ToolClientPort):
    def __init__(
        self,
        *,
        server_url: str,
        token: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        super().__init__(
            server_url=server_url,
            mode=ClientMode.REAL,
            headers=headers,
            http_client=http_client,
        )

    async def get_repo_snapshot(self, repo_url: str) -> RepoSnapshot:
        result = await self.call_tool("get_repo_snapshot", {"repo_url": repo_url})
        if not result.success or result.data is None:
            raise RuntimeError(result.error or {"message": "GitHub snapshot failed"})
        return RepoSnapshot.model_validate(result.data)

    async def create_issue(
        self,
        *,
        repo_url: str,
        title: str,
        body: str,
        labels: list[str],
        idempotency_key: str,
    ) -> ToolCallResult:
        return await self.call_tool(
            "create_issue",
            {
                "repo_url": repo_url,
                "title": title,
                "body": body,
                "labels": labels,
                "idempotency_key": idempotency_key,
            },
        )


class MockGitHubClient(ToolClientPort):
    def __init__(self, fixture_path: Path | None = None) -> None:
        self.fixture_path = fixture_path or Path(__file__).resolve().parents[3] / (
            "tests/fixtures/mock_repo_snapshot.json"
        )
        self.created_issues_by_key: dict[str, str] = {}

    @property
    def mode(self) -> ClientMode:
        return ClientMode.MOCK

    async def list_tools(self) -> list[ToolSpec]:
        self._log_mock()
        return [
            ToolSpec(
                name="get_repo_snapshot",
                description="Return repository metadata, tree, README, and CI signals.",
                input_schema={"type": "object", "required": ["repo_url"]},
            ),
            ToolSpec(
                name="create_issue",
                description="Create a GitHub issue using an idempotency key.",
                input_schema={"type": "object", "required": ["idempotency_key"]},
            ),
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> ToolCallResult:
        self._log_mock()
        if tool_name == "get_repo_snapshot":
            snapshot = self._load_snapshot()
            return ToolCallResult(success=True, data=snapshot)
        if tool_name == "create_issue":
            key = str(arguments["idempotency_key"])
            if key not in self.created_issues_by_key:
                issue_number = len(self.created_issues_by_key) + 1
                self.created_issues_by_key[key] = (
                    f"https://github.com/qurbaneliii/mock-repo/issues/{issue_number}"
                )
            return ToolCallResult(
                success=True,
                data={"url": self.created_issues_by_key[key]},
            )
        return ToolCallResult(
            success=False,
            error={"code": "UNKNOWN_TOOL", "message": f"Unknown tool: {tool_name}"},
        )

    async def get_repo_snapshot(self, repo_url: str) -> RepoSnapshot:
        result = await self.call_tool("get_repo_snapshot", {"repo_url": repo_url})
        return RepoSnapshot.model_validate(result.data)

    async def create_issue(
        self,
        *,
        repo_url: str,
        title: str,
        body: str,
        labels: list[str],
        idempotency_key: str,
    ) -> ToolCallResult:
        return await self.call_tool(
            "create_issue",
            {
                "repo_url": repo_url,
                "title": title,
                "body": body,
                "labels": labels,
                "idempotency_key": idempotency_key,
            },
        )

    def _load_snapshot(self) -> dict[str, Any]:
        return json.loads(self.fixture_path.read_text(encoding="utf-8"))

    def _log_mock(self) -> None:
        logger.info("MOCK_MODE_ACTIVE client=github")
