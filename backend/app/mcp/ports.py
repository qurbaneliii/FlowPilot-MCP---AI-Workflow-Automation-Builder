from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class ClientMode(str, Enum):
    REAL = "real"
    MOCK = "mock"
    UNAVAILABLE = "unavailable"


class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    input_schema: dict[str, Any]


class ToolCallResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    data: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class ToolClientPort(ABC):
    @property
    @abstractmethod
    def mode(self) -> ClientMode: ...

    @property
    def is_mock(self) -> bool:
        return self.mode == ClientMode.MOCK

    @abstractmethod
    async def list_tools(self) -> list[ToolSpec]: ...

    @abstractmethod
    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> ToolCallResult: ...
