class MCPClientError(Exception):
    """Base exception for MCP adapter failures."""


class ToolClientUnavailableError(MCPClientError):
    def __init__(self, client_name: str) -> None:
        self.client_name = client_name
        super().__init__(f"Tool client is unavailable: {client_name}")


class UnknownToolClientError(MCPClientError):
    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Unknown tool client: {name}")


class ToolCallError(MCPClientError):
    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool call failed for {tool_name}: {message}")
