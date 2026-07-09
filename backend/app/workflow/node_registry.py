from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from app.workflow.exceptions import DuplicateNodeTypeError, UnknownNodeTypeError

if TYPE_CHECKING:
    from app.workflow.nodes.base import NodeHandler


_REGISTRY: dict[str, type[Any]] = {}


def register_node(node_type: str) -> Callable[[type[Any]], type[Any]]:
    def decorator(handler_cls: type[Any]) -> type[Any]:
        if node_type in _REGISTRY:
            raise DuplicateNodeTypeError(node_type=node_type)
        _REGISTRY[node_type] = handler_cls
        return handler_cls

    return decorator


def get_handler(node_type: str) -> type["NodeHandler"]:
    try:
        return _REGISTRY[node_type]
    except KeyError as exc:
        raise UnknownNodeTypeError(node_type=node_type) from exc


def registered_node_types() -> list[str]:
    return sorted(_REGISTRY)
