class FlowPilotError(Exception):
    """Base exception for FlowPilot domain and service failures."""


class ConfigurationError(FlowPilotError):
    """Raised when required runtime configuration is invalid."""
