from typing import Literal

from app.core.config import Settings, get_settings
from app.mcp.clients.filesystem_client import FilesystemMCPClient, MockFilesystemClient
from app.mcp.clients.github_client import (
    GitHubMCPClient,
    GitHubRESTClient,
    MockGitHubClient,
)
from app.mcp.clients.openai_mcp_client import OpenAIMCPClient
from app.mcp.exceptions import UnknownToolClientError
from app.mcp.ports import ToolClientPort


ClientName = Literal["github", "filesystem", "openai_mcp"]


class ToolClientRegistry:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._clients: dict[str, ToolClientPort] = {
            "github": self._build_github_client(),
            "filesystem": self._build_filesystem_client(),
            "openai_mcp": OpenAIMCPClient(
                server_url=self.settings.openai_mcp_server_url,
                api_key=self.settings.openai_api_key,
            ),
        }

    def get_client(self, name: ClientName) -> ToolClientPort:
        try:
            return self._clients[name]
        except KeyError as exc:
            raise UnknownToolClientError(str(name)) from exc

    def _build_github_client(self) -> ToolClientPort:
        if self.settings.github_mcp_mode == "real":
            if self.settings.github_mcp_server_url:
                return GitHubMCPClient(
                    server_url=self.settings.github_mcp_server_url,
                    token=self.settings.github_token,
                )
            return GitHubRESTClient(token=self.settings.github_token)
        return MockGitHubClient()

    def _build_filesystem_client(self) -> ToolClientPort:
        if self.settings.filesystem_mcp_mode == "real":
            return FilesystemMCPClient(root=self.settings.filesystem_mcp_root)
        return MockFilesystemClient()


_REGISTRY: ToolClientRegistry | None = None


def get_registry() -> ToolClientRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ToolClientRegistry()
    return _REGISTRY


def get_client(name: ClientName) -> ToolClientPort:
    return get_registry().get_client(name)
