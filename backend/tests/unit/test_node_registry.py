import pytest

from app.workflow import node_registry
from app.workflow.exceptions import DuplicateNodeTypeError, UnknownNodeTypeError
from tests.fixtures.fake_node_handlers import NoOpSuccessHandler


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(node_registry, "_REGISTRY", {})


def test_register_and_retrieve_handler() -> None:
    node_registry.register_node("noop")(NoOpSuccessHandler)

    assert node_registry.get_handler("noop") is NoOpSuccessHandler


def test_duplicate_registration_raises_at_registration_time() -> None:
    node_registry.register_node("noop")(NoOpSuccessHandler)

    with pytest.raises(DuplicateNodeTypeError):
        node_registry.register_node("noop")(NoOpSuccessHandler)


def test_unknown_node_type_raises_on_lookup() -> None:
    with pytest.raises(UnknownNodeTypeError) as exc_info:
        node_registry.get_handler("missing")

    assert exc_info.value.node_type == "missing"
