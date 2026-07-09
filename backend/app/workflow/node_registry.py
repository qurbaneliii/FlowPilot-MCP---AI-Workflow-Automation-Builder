from collections.abc import Callable

from app.workflow.exceptions import DuplicateNodeTypeError, UnknownNodeTypeError
from app.workflow.nodes.base import NodeHandler


_REGISTRY: dict[str, type[NodeHandler]] = {}


def register_node(node_type: str) -> Callable[[type[NodeHandler]], type[NodeHandler]]:
    def decorator(handler_cls: type[NodeHandler]) -> type[NodeHandler]:
        if node_type in _REGISTRY:
            raise DuplicateNodeTypeError(node_type=node_type)
        _REGISTRY[node_type] = handler_cls
        return handler_cls

    return decorator


def get_handler(node_type: str) -> type[NodeHandler]:
    try:
        return _REGISTRY[node_type]
    except KeyError as exc:
        raise UnknownNodeTypeError(node_type=node_type) from exc
