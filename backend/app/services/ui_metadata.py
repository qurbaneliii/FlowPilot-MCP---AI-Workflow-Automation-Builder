from app.core.config import Settings, get_settings
from app.schemas.ui import (
    DemoModeResponse,
    ModeExplanationResponse,
    ModeExplanationsResponse,
)


def mode_explanations(settings: Settings | None = None) -> ModeExplanationsResponse:
    settings = settings or get_settings()
    mcp_mode = settings.github_mcp_mode
    agent_mode = settings.openai_agent_mode
    storage_mode = settings.effective_storage_mode
    return ModeExplanationsResponse(
        mcp=ModeExplanationResponse(
            mode=mcp_mode,
            label="Real GitHub" if mcp_mode == "real" else "Mock MCP",
            description=(
                "Live repository access is enabled. Approved GitHub writes use configured credentials."
                if mcp_mode == "real"
                else "Safe local mode. GitHub write actions return mock issue URLs instead of creating real issues."
            ),
        ),
        agent=ModeExplanationResponse(
            mode=agent_mode,
            label="Real OpenAI" if agent_mode == "real" else "Fake Agent",
            description=(
                "Live model analysis is enabled with the configured OpenAI credentials."
                if agent_mode == "real"
                else "Deterministic local AI responses are used. Configure OPENAI_API_KEY and real agent mode for live analysis."
            ),
        ),
        storage=ModeExplanationResponse(
            mode=storage_mode,
            label="Postgres" if storage_mode == "postgres" else "Memory Mode",
            description=(
                "Run history is stored persistently in Postgres."
                if storage_mode == "postgres"
                else "Run history resets when the backend restarts. Configure DATABASE_URL for persistent Postgres storage."
            ),
        ),
    )


def demo_mode(settings: Settings | None = None) -> DemoModeResponse:
    explanations = mode_explanations(settings)
    active = (
        explanations.mcp.mode != "real"
        or explanations.agent.mode != "real"
        or explanations.storage.mode != "postgres"
    )
    return DemoModeResponse(
        active=active,
        label="Demo mode active" if active else "Live mode active",
        description=(
            "FlowPilot is using safe local defaults. Real GitHub and OpenAI actions require explicit credentials."
            if active
            else "FlowPilot is using live GitHub and OpenAI services with persistent run storage."
        ),
    )
