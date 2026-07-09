import httpx
import pytest

from app.mcp.clients import openai_mcp_client as openai_mcp_module
from app.mcp.clients.filesystem_client import FilesystemMCPClient, MockFilesystemClient
from app.mcp.clients.github_client import GitHubMCPClient, MockGitHubClient
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
