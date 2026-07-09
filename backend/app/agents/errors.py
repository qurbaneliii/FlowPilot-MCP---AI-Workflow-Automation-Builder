class AgentError(Exception):
    """Base class for controlled agent-layer failures."""


class AgentNotConfiguredError(AgentError):
    def __init__(self, agent_name: str, reason: str | None = None) -> None:
        self.agent_name = agent_name
        self.reason = reason or "agent backend is not configured"
        super().__init__(f"{agent_name} is not configured: {self.reason}")


class AgentOutputValidationError(AgentError):
    def __init__(self, agent_name: str, validation_errors: str) -> None:
        self.agent_name = agent_name
        self.validation_errors = validation_errors
        super().__init__(f"{agent_name} returned invalid output: {validation_errors}")


class AgentPermanentError(AgentError):
    def __init__(self, agent_name: str, message: str) -> None:
        self.agent_name = agent_name
        super().__init__(f"{agent_name} failed permanently: {message}")
