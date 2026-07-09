from typing import Any

import httpx

from app.mcp.ports import ClientMode, ToolCallResult, ToolSpec


class JSONRPCMCPClient:
    def __init__(
        self,
        *,
        server_url: str,
        mode: ClientMode,
        headers: dict[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.server_url = server_url
        self._mode = mode
        self.headers = headers or {}
        self.http_client = http_client
        self._owns_client = http_client is None

    @property
    def mode(self) -> ClientMode:
        return self._mode

    async def list_tools(self) -> list[ToolSpec]:
        await self._request("initialize", {})
        response = await self._request("tools/list", {})
        tools = response.get("tools", [])
        return [
            ToolSpec(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("inputSchema", tool.get("input_schema", {})),
            )
            for tool in tools
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> ToolCallResult:
        response = await self._request(
            "tools/call",
            {"name": tool_name, "arguments": arguments},
        )
        if "error" in response:
            return ToolCallResult(success=False, error=response["error"])
        return ToolCallResult(success=True, data=response)

    async def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        client = self.http_client or httpx.AsyncClient(timeout=10)
        try:
            response = await client.post(
                self.server_url,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                headers=self.headers,
            )
            response.raise_for_status()
            payload = response.json()
            if "error" in payload:
                return {"error": payload["error"]}
            return payload.get("result", {})
        finally:
            if self._owns_client:
                await client.aclose()
