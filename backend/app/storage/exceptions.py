class StorageError(Exception):
    """Base class for persistence-layer errors."""


class RunNotFoundError(StorageError):
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        super().__init__(f"Run not found: {run_id}")


class WorkflowNotFoundError(StorageError):
    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"Workflow not found: {workflow_id}")


class ConcurrentModificationError(StorageError):
    def __init__(self, run_id: str, expected_version: int, actual_version: int) -> None:
        self.run_id = run_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Concurrent modification for run {run_id}: "
            f"expected version {expected_version}, found {actual_version}"
        )


class ApprovalNotFoundError(StorageError):
    def __init__(self, approval_id: str) -> None:
        self.approval_id = approval_id
        super().__init__(f"Approval not found: {approval_id}")


class ApprovalAlreadyResolvedError(StorageError):
    def __init__(self, approval_id: str, status: str) -> None:
        self.approval_id = approval_id
        self.status = status
        super().__init__(f"Approval {approval_id} is already resolved: {status}")
