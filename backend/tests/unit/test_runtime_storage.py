import pytest

from app.core.config import Settings
from app.services.runtime_storage import RuntimeStorage
from app.storage.repositories import (
    SQLAlchemyArtifactRepository,
    SQLAlchemyRunRepository,
    SQLAlchemyWorkflowRepository,
)


def test_api_uses_postgres_repository_when_database_url_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("STORAGE_MODE")
    storage = RuntimeStorage(
        Settings(database_url="postgresql+asyncpg://test:test@localhost/test")
    )

    assert storage.mode == "postgres"
    assert storage.persistent is True
    assert isinstance(storage.workflows, SQLAlchemyWorkflowRepository)
    assert isinstance(storage.runs, SQLAlchemyRunRepository)
    assert isinstance(storage.artifacts, SQLAlchemyArtifactRepository)


def test_api_uses_memory_store_only_when_storage_mode_memory() -> None:
    storage = RuntimeStorage(
        Settings(
            storage_mode="memory",
            database_url="postgresql+asyncpg://test:test@localhost/test",
        )
    )

    assert storage.mode == "memory"
    assert storage.persistent is False
