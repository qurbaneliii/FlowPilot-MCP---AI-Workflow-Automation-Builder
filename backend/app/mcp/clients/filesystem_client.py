import logging
from pathlib import Path
from typing import Any

from app.mcp.ports import ClientMode, ToolCallResult, ToolClientPort, ToolSpec


logger = logging.getLogger(__name__)


class FilesystemMCPClient(ToolClientPort):
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()

    @property
    def mode(self) -> ClientMode:
        return ClientMode.REAL

    async def list_tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="read_file",
                description="Read a UTF-8 text file under the configured root.",
                input_schema={"type": "object", "required": ["path"]},
            ),
            ToolSpec(
                name="list_directory",
                description="List files and directories under the configured root.",
                input_schema={"type": "object", "required": ["path"]},
            ),
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> ToolCallResult:
        try:
            path = self._resolve(str(arguments.get("path", ".")))
            if tool_name == "read_file":
                return ToolCallResult(success=True, data={"content": path.read_text()})
            if tool_name == "list_directory":
                return ToolCallResult(
                    success=True,
                    data={"entries": sorted(child.name for child in path.iterdir())},
                )
        except Exception as exc:
            return ToolCallResult(
                success=False,
                error={"code": exc.__class__.__name__, "message": str(exc)},
            )
        return ToolCallResult(
            success=False,
            error={"code": "UNKNOWN_TOOL", "message": f"Unknown tool: {tool_name}"},
        )

    def _resolve(self, path: str) -> Path:
        candidate = (self.root / path).resolve()
        if not candidate.is_relative_to(self.root):
            raise PermissionError("Path escapes configured filesystem root")
        return candidate


class MockFilesystemClient(ToolClientPort):
    def __init__(self, files: dict[str, str] | None = None) -> None:
        self.files = files or {
            "README.md": "# Mock Repo\n\nUsage instructions.",
            "src/app.py": "print('hello')\n",
        }

    @property
    def mode(self) -> ClientMode:
        return ClientMode.MOCK

    async def list_tools(self) -> list[ToolSpec]:
        self._log_mock()
        return [
            ToolSpec(
                name="read_file",
                description="Read a file from the in-memory filesystem.",
                input_schema={"type": "object", "required": ["path"]},
            ),
            ToolSpec(
                name="list_directory",
                description="List the in-memory file tree.",
                input_schema={"type": "object"},
            ),
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> ToolCallResult:
        self._log_mock()
        if tool_name == "read_file":
            path = str(arguments["path"])
            if path not in self.files:
                return ToolCallResult(
                    success=False,
                    error={"code": "FILE_NOT_FOUND", "message": path},
                )
            return ToolCallResult(success=True, data={"content": self.files[path]})
        if tool_name == "list_directory":
            return ToolCallResult(success=True, data={"entries": sorted(self.files)})
        return ToolCallResult(
            success=False,
            error={"code": "UNKNOWN_TOOL", "message": f"Unknown tool: {tool_name}"},
        )

    def _log_mock(self) -> None:
        logger.info("MOCK_MODE_ACTIVE client=filesystem")
