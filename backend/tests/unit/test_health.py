import pytest
from fastapi.testclient import TestClient

from app.api.v1 import health as health_module
from app.core.config import Settings
from app.main import create_app


class _AsyncConnection:
    async def execute(self, statement: object) -> None:
        return None


class _ConnectContext:
    async def __aenter__(self) -> _AsyncConnection:
        return _AsyncConnection()

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class _ReachableEngine:
    def connect(self) -> _ConnectContext:
        return _ConnectContext()


class _BrokenConnectContext:
    async def __aenter__(self) -> _AsyncConnection:
        raise ConnectionError("database unavailable")

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class _UnreachableEngine:
    def connect(self) -> _BrokenConnectContext:
        return _BrokenConnectContext()


@pytest.mark.asyncio
async def test_check_database_returns_ok_when_query_succeeds() -> None:
    status = await health_module.check_database(
        database_engine=_ReachableEngine(), timeout_seconds=0.1
    )

    assert status == "ok"


@pytest.mark.asyncio
async def test_check_database_returns_error_when_query_fails() -> None:
    status = await health_module.check_database(
        database_engine=_UnreachableEngine(), timeout_seconds=0.1
    )

    assert status == "error"


@pytest.mark.asyncio
async def test_check_openai_returns_not_configured_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        health_module, "get_settings", lambda: Settings(openai_api_key=None)
    )

    status = await health_module.check_openai()

    assert status == "not_configured"


@pytest.mark.asyncio
async def test_check_openai_returns_ok_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        health_module, "get_settings", lambda: Settings(openai_api_key="test-key")
    )

    status = await health_module.check_openai()

    assert status == "ok"


def test_health_endpoint_returns_200_when_dependencies_degraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def degraded_database() -> str:
        return "error"

    async def unconfigured_openai() -> str:
        return "not_configured"

    monkeypatch.setattr(health_module, "check_database", degraded_database)
    monkeypatch.setattr(health_module, "check_openai", unconfigured_openai)
    monkeypatch.setattr(
        health_module, "get_settings", lambda: Settings(app_version="test")
    )

    client = TestClient(create_app())
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "test"
    assert body["dependencies"] == {"database": "error", "openai": "not_configured"}
    assert body["services"]["database"]["label"] == "Memory mode"
    assert body["services"]["database"]["blocking"] is False
    assert body["ui"]["database_warning_blocks_demo"] is False


def test_health_endpoint_returns_200_when_dependencies_healthy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def reachable_database() -> str:
        return "ok"

    async def configured_openai() -> str:
        return "ok"

    monkeypatch.setattr(health_module, "check_database", reachable_database)
    monkeypatch.setattr(health_module, "check_openai", configured_openai)
    monkeypatch.setattr(
        health_module, "get_settings", lambda: Settings(app_version="test")
    )

    client = TestClient(create_app())
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "test"
    assert body["dependencies"] == {"database": "ok", "openai": "ok"}
    assert body["services"]["backend"]["label"] == "Backend connected"
    assert body["services"]["database"]["label"] == "Database connected"


def test_health_response_contains_ui_status_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def degraded_database() -> str:
        return "error"

    async def unconfigured_openai() -> str:
        return "not_configured"

    monkeypatch.setattr(health_module, "check_database", degraded_database)
    monkeypatch.setattr(health_module, "check_openai", unconfigured_openai)
    monkeypatch.setattr(
        health_module, "get_settings", lambda: Settings(app_version="test")
    )

    response = TestClient(create_app()).get("/api/v1/health")
    body = response.json()

    assert body["services"]["backend"]["label"] == "Backend connected"
    assert body["services"]["database"]["label"] == "Memory mode"
    assert body["services"]["mcp"]["label"] == "Mock MCP"
    assert body["services"]["openai"]["label"] == "Fake agent mode"
    assert body["ui"]["storage_mode_label"] == "Memory mode"
