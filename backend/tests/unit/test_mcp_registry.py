from pathlib import Path

import pytest

from app.core.config import Settings
from app.mcp.clients.filesystem_client import FilesystemMCPClient, MockFilesystemClient
from app.mcp.clients.github_client import GitHubMCPClient, MockGitHubClient
from app.mcp.exceptions import UnknownToolClientError
from app.mcp.ports import ClientMode
from app.mcp.registry import ToolClientRegistry


def test_registry_resolves_mock_by_default_without_mode_env() -> None:
    registry = ToolClientRegistry(Settings(openai_api_key=None))

    assert isinstance(registry.get_client("github"), MockGitHubClient)
    assert isinstance(registry.get_client("filesystem"), MockFilesystemClient)
    assert registry.get_client("github").mode == ClientMode.MOCK


def test_registry_resolves_real_when_mode_env_set_to_real() -> None:
    registry = ToolClientRegistry(
        Settings(
            github_mcp_mode="real",
            github_mcp_server_url="http://github-mcp.test/mcp",
            filesystem_mcp_mode="real",
            filesystem_mcp_root=".",
            openai_api_key=None,
        )
    )

    assert isinstance(registry.get_client("github"), GitHubMCPClient)
    assert isinstance(registry.get_client("filesystem"), FilesystemMCPClient)
    assert registry.get_client("github").mode == ClientMode.REAL


def test_registry_unknown_client_name_raises() -> None:
    registry = ToolClientRegistry(Settings(openai_api_key=None))

    with pytest.raises(UnknownToolClientError):
        registry.get_client("missing")  # type: ignore[arg-type]


def test_registry_is_sole_mode_branching_point() -> None:
    mcp_root = Path(__file__).resolve().parents[2] / "app" / "mcp"
    offenders: list[Path] = []
    for path in mcp_root.rglob("*.py"):
        if path.name == "registry.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "github_mcp_mode" in text or "filesystem_mcp_mode" in text:
            offenders.append(path)

    assert offenders == []
