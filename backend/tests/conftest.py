import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


_INTEGRATION_SKIPS_IN_CI: list[str] = []


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
