import json
import logging
from pathlib import Path
import re
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

from app.mcp.clients.base_http import JSONRPCMCPClient
from app.mcp.ports import ClientMode, ToolCallResult, ToolClientPort, ToolSpec


logger = logging.getLogger(__name__)

GITHUB_REPO_URL = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


def parse_github_repo_url(repo_url: str) -> tuple[str, str]:
    match = GITHUB_REPO_URL.fullmatch(repo_url.strip())
    if match is None:
        raise ValueError("Repository URL must be a GitHub owner/repo URL.")
    return match.group("owner"), match.group("repo")


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


class GitHubRESTClient(ToolClientPort):
    """Built-in GitHub REST adapter for public reads and approved writes."""

    def __init__(
        self,
        *,
        token: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        api_url: str = "https://api.github.com",
    ) -> None:
        self.token = token
        self.http_client = http_client
        self.api_url = api_url.rstrip("/")
        self._owns_client = http_client is None
        self.created_issues_by_key: dict[str, str] = {}

    @property
    def mode(self) -> ClientMode:
        return ClientMode.REAL

    async def list_tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="get_repo_snapshot",
                description="Read repository metadata, README, and recursive file tree.",
                input_schema={"type": "object", "required": ["repo_url"]},
            ),
            ToolSpec(
                name="create_issue",
                description="Create an idempotent GitHub issue after application approval.",
                input_schema={
                    "type": "object",
                    "required": ["repo_url", "title", "body", "idempotency_key"],
                },
            ),
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> ToolCallResult:
        try:
            if tool_name == "get_repo_snapshot":
                snapshot = await self.get_repo_snapshot(str(arguments["repo_url"]))
                return ToolCallResult(
                    success=True, data=snapshot.model_dump(mode="json")
                )
            if tool_name == "create_issue":
                return await self.create_issue(
                    repo_url=str(arguments["repo_url"]),
                    title=str(arguments["title"]),
                    body=str(arguments.get("body") or ""),
                    labels=[str(label) for label in arguments.get("labels", [])],
                    idempotency_key=str(arguments["idempotency_key"]),
                )
        except ValueError as exc:
            return ToolCallResult(
                success=False,
                error={"code": "INVALID_REPO_URL", "message": str(exc)},
            )
        return ToolCallResult(
            success=False,
            error={"code": "UNKNOWN_TOOL", "message": f"Unknown tool: {tool_name}"},
        )

    async def get_repo_snapshot(self, repo_url: str) -> RepoSnapshot:
        owner, repo = parse_github_repo_url(repo_url)
        client = self.http_client or httpx.AsyncClient(timeout=15)
        headers = self._headers()
        try:
            metadata_response = await client.get(
                f"{self.api_url}/repos/{owner}/{repo}", headers=headers
            )
            self._raise_read_error(metadata_response)
            metadata = metadata_response.json()
            branch = str(metadata.get("default_branch") or "main")
            tree_response = await client.get(
                f"{self.api_url}/repos/{owner}/{repo}/git/trees/{branch}",
                params={"recursive": "1"},
                headers=headers,
            )
            self._raise_read_error(tree_response)
            file_tree = [
                str(item["path"])
                for item in tree_response.json().get("tree", [])
                if item.get("type") == "blob" and item.get("path")
            ]
            readme_response = await client.get(
                f"{self.api_url}/repos/{owner}/{repo}/readme",
                headers={**headers, "Accept": "application/vnd.github.raw+json"},
            )
            if readme_response.status_code == 404:
                readme = None
            else:
                self._raise_read_error(readme_response)
                readme = readme_response.text
            normalized_url = f"https://github.com/{owner}/{repo}"
            return RepoSnapshot(
                repo_url=normalized_url,
                metadata={
                    "owner": owner,
                    "name": repo,
                    "full_name": metadata.get("full_name", f"{owner}/{repo}"),
                    "description": metadata.get("description"),
                    "default_branch": branch,
                    "stars": metadata.get("stargazers_count", 0),
                    "forks": metadata.get("forks_count", 0),
                    "open_issues": metadata.get("open_issues_count", 0),
                    "visibility": metadata.get("visibility", "public"),
                    "html_url": metadata.get("html_url", normalized_url),
                },
                file_tree=file_tree,
                readme=readme,
                env_example_present=any(
                    path.lower() in {".env.example", ".env.sample"}
                    for path in file_tree
                ),
                workflows=[
                    path for path in file_tree if path.startswith(".github/workflows/")
                ],
            )
        finally:
            if self._owns_client:
                await client.aclose()

    async def create_issue(
        self,
        *,
        repo_url: str,
        title: str,
        body: str,
        labels: list[str],
        idempotency_key: str,
    ) -> ToolCallResult:
        if not self.token:
            return ToolCallResult(
                success=False,
                error={
                    "code": "GITHUB_TOKEN_REQUIRED",
                    "message": "Real GitHub issue creation requires GITHUB_TOKEN.",
                },
            )
        if idempotency_key in self.created_issues_by_key:
            return ToolCallResult(
                success=True,
                data={
                    "url": self.created_issues_by_key[idempotency_key],
                    "reused": True,
                },
            )
        try:
            owner, repo = parse_github_repo_url(repo_url)
        except ValueError as exc:
            return ToolCallResult(
                success=False,
                error={"code": "INVALID_REPO_URL", "message": str(exc)},
            )
        marker = f"<!-- flowpilot-idempotency:{idempotency_key} -->"
        client = self.http_client or httpx.AsyncClient(timeout=15)
        headers = self._headers()
        try:
            existing = await client.get(
                f"{self.api_url}/repos/{owner}/{repo}/issues",
                params={"state": "all", "per_page": "100"},
                headers=headers,
            )
            if existing.status_code == 200:
                for issue in existing.json():
                    if marker in str(issue.get("body") or ""):
                        url = str(issue.get("html_url") or "")
                        self.created_issues_by_key[idempotency_key] = url
                        return ToolCallResult(
                            success=True, data={"url": url, "reused": True}
                        )
            response = await client.post(
                f"{self.api_url}/repos/{owner}/{repo}/issues",
                json={"title": title, "body": f"{body}\n\n{marker}", "labels": labels},
                headers=headers,
            )
            if response.status_code not in {200, 201}:
                return ToolCallResult(success=False, error=self._write_error(response))
            url = str(response.json().get("html_url") or "")
            self.created_issues_by_key[idempotency_key] = url
            return ToolCallResult(success=True, data={"url": url, "reused": False})
        finally:
            if self._owns_client:
                await client.aclose()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "FlowPilot-MCP",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @staticmethod
    def _raise_read_error(response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        if response.status_code == 401:
            raise RuntimeError("GitHub authentication failed.")
        if (
            response.status_code == 403
            and response.headers.get("x-ratelimit-remaining") == "0"
        ):
            raise RuntimeError("GitHub API rate limit exceeded.")
        if response.status_code == 404:
            raise RuntimeError("GitHub repository was not found or is not accessible.")
        raise RuntimeError("GitHub repository read failed.")

    @staticmethod
    def _write_error(response: httpx.Response) -> dict[str, str]:
        if response.status_code == 401:
            code = "GITHUB_AUTH_FAILED"
            message = "GitHub authentication failed."
        elif response.status_code == 403:
            code = "GITHUB_PERMISSION_DENIED"
            message = "GitHub token cannot create issues in this repository."
        else:
            code = "GITHUB_ISSUE_CREATE_FAILED"
            message = "GitHub issue creation failed."
        return {"code": code, "message": message}


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
