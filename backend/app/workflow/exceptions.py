class WorkflowDomainError(Exception):
    """Base class for framework-independent workflow domain errors."""


class GraphValidationError(WorkflowDomainError):
    """Base class for graph validation failures."""


class DuplicateNodeIdError(GraphValidationError):
    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"Duplicate node id: {node_id}")


class DanglingDependencyError(GraphValidationError):
    def __init__(self, node_id: str, missing_dependency: str) -> None:
        self.node_id = node_id
        self.missing_dependency = missing_dependency
        super().__init__(f"Node {node_id} depends on missing node {missing_dependency}")


class GraphCycleError(GraphValidationError):
    def __init__(self, cycle_path: list[str]) -> None:
        self.cycle_path = cycle_path
        super().__init__(f"Graph cycle detected: {' -> '.join(cycle_path)}")


class NodeRegistryError(WorkflowDomainError):
    """Base class for node registry failures."""


class DuplicateNodeTypeError(NodeRegistryError):
    def __init__(self, node_type: str) -> None:
        self.node_type = node_type
        super().__init__(f"Duplicate node type registered: {node_type}")


class UnknownNodeTypeError(NodeRegistryError):
    def __init__(self, node_type: str) -> None:
        self.node_type = node_type
        super().__init__(f"Unknown node type: {node_type}")


class InvalidStateTransitionError(WorkflowDomainError):
    def __init__(self, from_status: str, to_status: str, node_id: str) -> None:
        self.from_status = from_status
        self.to_status = to_status
        self.node_id = node_id
        super().__init__(
            f"Invalid transition for {node_id}: {from_status} -> {to_status}"
        )


class InvalidResumeStateError(WorkflowDomainError):
    def __init__(self, node_id: str, status: str) -> None:
        self.node_id = node_id
        self.status = status
        super().__init__(f"Node {node_id} is not waiting for approval: {status}")


class TransientError(WorkflowDomainError):
    """An execution error that may succeed on a later attempt."""


class PermanentError(WorkflowDomainError):
    """An execution error that must not be retried."""


class RetryExhaustedError(WorkflowDomainError):
    def __init__(self, last_error: Exception) -> None:
        self.last_error = last_error
        super().__init__(f"Retry attempts exhausted: {last_error}")


class NodeTimeoutError(TransientError):
    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Node execution timed out after {timeout_seconds} seconds")
