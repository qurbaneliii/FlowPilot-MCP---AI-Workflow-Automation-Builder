import logging
from typing import Any

import httpx

from app.mcp.clients.base_http import JSONRPCMCPClient
from app.mcp.exceptions import ToolClientUnavailableError
from app.mcp.ports import ClientMode, ToolCallResult, ToolClientPort, ToolSpec


logger = logging.getLogger(__name__)


class OpenAIMCPClient(ToolClientPort):
    _warning_logged = False

    def __init__(
        self,
        *,
        server_url: str | None,
        api_key: str | None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.server_url = server_url
        self.api_key = api_key
        if server_url and api_key:
            self._mode = ClientMode.REAL
            self._client = JSONRPCMCPClient(
                server_url=server_url,
                mode=ClientMode.REAL,
                headers={"Authorization": f"Bearer {api_key}"},
                http_client=http_client,
            )
        else:
            self._mode = ClientMode.UNAVAILABLE
            self._client = None
            self._log_unavailable_once()

    @property
    def mode(self) -> ClientMode:
        return self._mode

    async def list_tools(self) -> list[ToolSpec]:
        if self._client is None:
            return []
        return await self._client.list_tools()

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> ToolCallResult:
        if self._client is None:
            raise ToolClientUnavailableError("openai_mcp")
        return await self._client.call_tool(tool_name, arguments)

    @classmethod
    def reset_warning_state_for_tests(cls) -> None:
        cls._warning_logged = False

    @classmethod
    def _log_unavailable_once(cls) -> None:
        if cls._warning_logged:
            return
        logger.warning("OPENAI_MCP_NOT_CONFIGURED")
        cls._warning_logged = True
