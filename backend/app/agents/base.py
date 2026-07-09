from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel


class AgentPort(ABC):
    output_schema: ClassVar[type[BaseModel]]

    @abstractmethod
    async def run(self, input_payload: dict[str, Any]) -> BaseModel: ...
