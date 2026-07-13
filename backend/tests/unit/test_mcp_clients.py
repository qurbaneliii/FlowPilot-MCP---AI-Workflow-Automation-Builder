import httpx
import pytest

from app.mcp.clients import openai_mcp_client as openai_mcp_module
from app.mcp.clients.filesystem_client import FilesystemMCPClient, MockFilesystemClient
from app.mcp.clients.github_client import (
    GitHubMCPClient,
    GitHubRESTClient,
    MockGitHubClient,
    parse_github_repo_url,
)
from app.mcp.clients.openai_mcp_client import OpenAIMCPClient
from app.mcp.exceptions import ToolClientUnavailableError
from app.mcp.ports import ClientMode, ToolClientPort
from tests.fixtures.fake_mcp_server import create_fake_mcp_app


@pytest.mark.asyncio
async def test_github_client_mock_returns_realistic_snapshot() -> None:
    client = MockGitHubClient()

    snapshot = await client.get_repo_snapshot(
        "https://github.com/qurbaneliii/mock-repo"
    )

    assert snapshot.metadata["name"] == "mock-repo"
    assert ".github/workflows/ci.yml" in snapshot.file_tree
    assert snapshot.env_example_present is False


@pytest.mark.asyncio
async def test_github_client_mock_create_issue_idempotent_on_same_key() -> None:
    client = MockGitHubClient()

    first = await client.create_issue(
        repo_url="https://github.com/qurbaneliii/mock-repo",
        title="Fix README",
        body="Body",
        labels=["warning"],
        idempotency_key="run-node-finding",
    )
    second = await client.create_issue(
        repo_url="https://github.com/qurbaneliii/mock-repo",
        title="Fix README",
        body="Body",
        labels=["warning"],
        idempotency_key="run-node-finding",
    )

    assert first.data == second.data
    assert len(client.created_issues_by_key) == 1


@pytest.mark.asyncio
async def test_github_client_mock_create_issue_distinct_for_different_keys() -> None:
    client = MockGitHubClient()

    first = await client.create_issue(
        repo_url="https://github.com/qurbaneliii/mock-repo",
        title="Fix README",
        body="Body",
        labels=["warning"],
        idempotency_key="one",
    )
    second = await client.create_issue(
        repo_url="https://github.com/qurbaneliii/mock-repo",
        title="Add tests",
        body="Body",
        labels=["warning"],
        idempotency_key="two",
    )

    assert first.data != second.data
    assert len(client.created_issues_by_key) == 2


def test_real_github_url_parser() -> None:
    assert parse_github_repo_url("https://github.com/openai/openai-python.git") == (
        "openai",
        "openai-python",
    )
    with pytest.raises(ValueError):
        parse_github_repo_url("https://example.com/openai/openai-python")


@pytest.mark.asyncio
async def test_github_reader_public_repo_snapshot_contract() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/repos/openai/openai-python"):
            return httpx.Response(
                200,
                json={
                    "full_name": "openai/openai-python",
                    "default_branch": "main",
                    "stargazers_count": 100,
                    "forks_count": 10,
                    "open_issues_count": 2,
                    "html_url": "https://github.com/openai/openai-python",
                },
            )
        if "/git/trees/main" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "tree": [
                        {"path": "README.md", "type": "blob"},
                        {"path": "pyproject.toml", "type": "blob"},
                        {"path": "tests/test_client.py", "type": "blob"},
                        {"path": ".github/workflows/ci.yml", "type": "blob"},
                        {"path": ".env.example", "type": "blob"},
                    ]
                },
            )
        if request.url.path.endswith("/readme"):
            return httpx.Response(200, text="# OpenAI Python")
        raise AssertionError(f"Unexpected request: {request.url}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        snapshot = await GitHubRESTClient(http_client=http_client).get_repo_snapshot(
            "https://github.com/openai/openai-python"
        )

    assert snapshot.metadata["owner"] == "openai"
    assert snapshot.metadata["name"] == "openai-python"
    assert snapshot.readme == "# OpenAI Python"
    assert snapshot.env_example_present is True
    assert snapshot.workflows == [".github/workflows/ci.yml"]
    assert len(snapshot.file_tree) == 5


@pytest.mark.asyncio
async def test_github_reader_missing_readme_is_not_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/readme"):
            return httpx.Response(404)
        if "/git/trees/" in request.url.path:
            return httpx.Response(200, json={"tree": []})
        return httpx.Response(200, json={"default_branch": "main"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        snapshot = await GitHubRESTClient(http_client=http_client).get_repo_snapshot(
            "https://github.com/example/no-readme"
        )
    assert snapshot.readme is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "headers", "message"),
    [
        (401, {}, "authentication failed"),
        (403, {"x-ratelimit-remaining": "0"}, "rate limit exceeded"),
    ],
)
async def test_github_reader_provider_errors_are_controlled(
    status: int, headers: dict[str, str], message: str
) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status, headers=headers)
        )
    ) as http_client:
        with pytest.raises(RuntimeError, match=message):
            await GitHubRESTClient(http_client=http_client).get_repo_snapshot(
                "https://github.com/example/repo"
            )


@pytest.mark.asyncio
async def test_issue_creator_real_mode_requires_token() -> None:
    result = await GitHubRESTClient().create_issue(
        repo_url="https://github.com/example/repo",
        title="Improve README",
        body="Details",
        labels=[],
        idempotency_key="run:node:key",
    )
    assert result.error == {
        "code": "GITHUB_TOKEN_REQUIRED",
        "message": "Real GitHub issue creation requires GITHUB_TOKEN.",
    }


@pytest.mark.asyncio
async def test_issue_creator_real_mode_is_idempotent() -> None:
    calls = {"posts": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json=[])
        calls["posts"] += 1
        return httpx.Response(
            201, json={"html_url": "https://github.com/example/repo/issues/1"}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = GitHubRESTClient(token="test-token", http_client=http_client)
        kwargs = {
            "repo_url": "https://github.com/example/repo",
            "title": "Improve README",
            "body": "Details",
            "labels": ["documentation"],
            "idempotency_key": "run:node:key",
        }
        first = await client.create_issue(**kwargs)
        second = await client.create_issue(**kwargs)

    assert first.data["url"] == second.data["url"]
    assert second.data["reused"] is True
    assert calls["posts"] == 1


@pytest.mark.asyncio
async def test_filesystem_client_mock_reads_fixture_tree() -> None:
    client = MockFilesystemClient({"README.md": "# Hello", "src/app.py": "print(1)"})

    listing = await client.call_tool("list_directory", {})
    readme = await client.call_tool("read_file", {"path": "README.md"})

    assert listing.success is True
    assert listing.data == {"entries": ["README.md", "src/app.py"]}
    assert readme.data == {"content": "# Hello"}


@pytest.mark.asyncio
async def test_openai_mcp_client_unavailable_mode_when_url_unset() -> None:
    OpenAIMCPClient.reset_warning_state_for_tests()
    client = OpenAIMCPClient(server_url=None, api_key="key")

    assert client.mode == ClientMode.UNAVAILABLE
    assert client.is_mock is False
    assert await client.list_tools() == []


def test_openai_mcp_client_unavailable_mode_logs_warning_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    OpenAIMCPClient.reset_warning_state_for_tests()
    warnings: list[str] = []
    monkeypatch.setattr(
        openai_mcp_module.logger,
        "warning",
        lambda message: warnings.append(message),
    )

    OpenAIMCPClient(server_url=None, api_key=None)
    OpenAIMCPClient(server_url=None, api_key=None)

    assert warnings == ["OPENAI_MCP_NOT_CONFIGURED"]


@pytest.mark.asyncio
async def test_openai_mcp_client_call_tool_raises_when_unavailable() -> None:
    OpenAIMCPClient.reset_warning_state_for_tests()
    client = OpenAIMCPClient(server_url=None, api_key=None)

    with pytest.raises(ToolClientUnavailableError):
        await client.call_tool("dummy_tool", {})


@pytest.mark.asyncio
async def test_openai_mcp_client_handshake_against_fake_server() -> None:
    app = create_fake_mcp_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as http_client:
        client = OpenAIMCPClient(
            server_url="http://testserver/mcp",
            api_key="test-key",
            http_client=http_client,
        )

        result = await client.call_tool("dummy_tool", {"value": "hello"})

    assert result.success is True
    assert result.data == {"tool": "dummy_tool", "arguments": {"value": "hello"}}


@pytest.mark.asyncio
async def test_openai_mcp_client_list_tools_reflects_server_advertised_tools() -> None:
    app = create_fake_mcp_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as http_client:
        client = OpenAIMCPClient(
            server_url="http://testserver/mcp",
            api_key="test-key",
            http_client=http_client,
        )

        tools = await client.list_tools()

    assert [tool.name for tool in tools] == ["dummy_tool"]
    assert tools[0].input_schema["properties"]["value"]["type"] == "string"


@pytest.mark.parametrize(
    "client",
    [
        MockGitHubClient(),
        GitHubMCPClient(server_url="http://example.test/mcp"),
        GitHubRESTClient(),
        MockFilesystemClient(),
        FilesystemMCPClient(root="."),
        OpenAIMCPClient(server_url=None, api_key=None),
    ],
)
def test_tool_client_port_contract_satisfied_by_all_concrete_clients(
    client: ToolClientPort,
) -> None:
    assert isinstance(client, ToolClientPort)
    assert hasattr(client, "list_tools")
    assert hasattr(client, "call_tool")
    assert isinstance(client.is_mock, bool)
