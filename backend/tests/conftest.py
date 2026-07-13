import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.services.runtime_storage import reset_runtime_storage

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


_INTEGRATION_SKIPS_IN_CI: list[str] = []


@pytest.fixture(autouse=True)
def force_unit_tests_to_explicit_memory_mode(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    if "tests/unit/" not in request.node.nodeid.replace("\\", "/"):
        yield
        return
    monkeypatch.setenv("STORAGE_MODE", "memory")
    get_settings.cache_clear()
    reset_runtime_storage()
    yield
    reset_runtime_storage()
    get_settings.cache_clear()


def pytest_configure(config: pytest.Config) -> None:
    _INTEGRATION_SKIPS_IN_CI.clear()


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if os.environ.get("CI", "").lower() != "true":
        return
    if "tests/integration/" not in report.nodeid.replace("\\", "/"):
        return
    if report.skipped:
        _INTEGRATION_SKIPS_IN_CI.append(report.nodeid)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if os.environ.get("CI", "").lower() != "true":
        return
    if _INTEGRATION_SKIPS_IN_CI:
        terminal = session.config.pluginmanager.get_plugin("terminalreporter")
        if terminal is not None:
            terminal.write_sep(
                "!",
                "Integration tests skipped in CI - Postgres service container not reachable, this must never pass silently.",
            )
            for nodeid in _INTEGRATION_SKIPS_IN_CI:
                terminal.write_line(f"skipped: {nodeid}")
        session.exitstatus = 1
