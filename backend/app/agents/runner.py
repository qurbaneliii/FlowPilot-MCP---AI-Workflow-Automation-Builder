import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from app.agents.backends import (
    AgentBackendMode,
    AgentBackendPort,
    FakeAgentBackend,
    OpenAIAgentBackend,
    UnavailableAgentBackend,
)
from app.agents.errors import AgentNotConfiguredError, AgentOutputValidationError
from app.core.config import Settings, get_settings
from app.workflow.exceptions import TransientError
from app.workflow.utils.retry import with_retry
from app.workflow.utils.timeout import with_timeout


logger = logging.getLogger(__name__)


class AgentRunner:
    def __init__(
        self,
        *,
        agent_name: str,
        output_schema: type[BaseModel],
        backend: AgentBackendPort | None = None,
        settings: Settings | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.agent_name = agent_name
        self.output_schema = output_schema
        self.settings = settings or get_settings()
        self.backend = backend or self._build_backend_from_settings()
        self.timeout_seconds = timeout_seconds

    async def run(self, input_payload: dict[str, Any]) -> BaseModel:
        if (
            self.backend.mode == AgentBackendMode.REAL
            and not self.settings.openai_api_key
        ):
            raise AgentNotConfiguredError(self.agent_name, "OPENAI_API_KEY is missing")
        system_prompt = self._load_prompt()
        logger.info("agent_invocation_started agent=%s", self.agent_name)
        raw = await self._invoke_backend(system_prompt, input_payload, None)
        try:
            validated = self.output_schema.model_validate(raw)
        except ValidationError as exc:
            validation_error = str(exc)
            logger.info("agent_reprompt agent=%s", self.agent_name)
            raw = await self._invoke_backend(
                system_prompt, input_payload, validation_error
            )
            try:
                validated = self.output_schema.model_validate(raw)
            except ValidationError as second_exc:
                raise AgentOutputValidationError(
                    self.agent_name, str(second_exc)
                ) from second_exc
        logger.info("agent_invocation_completed agent=%s", self.agent_name)
        return validated

    async def _invoke_backend(
        self,
        system_prompt: str,
        input_payload: dict[str, Any],
        validation_error: str | None,
    ) -> dict[str, Any]:
        return await with_retry(
            lambda: with_timeout(
                lambda: self.backend.invoke(
                    agent_name=self.agent_name,
                    system_prompt=system_prompt,
                    input_payload=input_payload,
                    validation_error=validation_error,
                ),
                timeout_seconds=self.timeout_seconds,
            ),
            max_attempts=3,
            base_delay=0,
            retryable_exceptions=(TransientError,),
        )

    def _load_prompt(self) -> str:
        prompt_path = (
            Path(__file__).resolve().parent / "prompts" / self.agent_name / "v1.md"
        )
        return prompt_path.read_text(encoding="utf-8")

    def _build_backend_from_settings(self) -> AgentBackendPort:
        mode = self.settings.openai_agent_mode.lower()
        if mode == AgentBackendMode.FAKE.value:
            return FakeAgentBackend()
        if mode == AgentBackendMode.UNAVAILABLE.value:
            return UnavailableAgentBackend()
        if mode == AgentBackendMode.REAL.value:
            return OpenAIAgentBackend(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_agent_model,
            )
        raise AgentNotConfiguredError(
            self.agent_name,
            f"unsupported OPENAI_AGENT_MODE '{self.settings.openai_agent_mode}'",
        )
