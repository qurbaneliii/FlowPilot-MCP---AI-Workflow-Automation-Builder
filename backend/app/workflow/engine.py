from collections import deque
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Literal

from app.workflow.exceptions import (
    InvalidResumeStateError,
    InvalidStateTransitionError,
    NodeRegistryError,
    PermanentError,
    RetryExhaustedError,
    TransientError,
    WorkflowDomainError,
)
from app.workflow.graph import NodeDefinition, validate_and_sort
from app.workflow.input_resolution import resolve_node_inputs
from app.workflow.node_registry import get_handler
from app.workflow.nodes.base import NodeExecutionContext, NodeExecutionResult
from app.workflow.state import NodeExecutionState, NodeStatus, RunState
from app.workflow.utils.retry import with_retry
from app.workflow.utils.timeout import with_timeout


ALLOWED_TRANSITIONS: dict[NodeStatus, set[NodeStatus]] = {
    NodeStatus.PENDING: {NodeStatus.RUNNING, NodeStatus.SKIPPED},
    NodeStatus.RUNNING: {
        NodeStatus.COMPLETED,
        NodeStatus.FAILED,
        NodeStatus.WAITING_FOR_APPROVAL,
    },
    NodeStatus.WAITING_FOR_APPROVAL: {NodeStatus.RUNNING, NodeStatus.SKIPPED},
    NodeStatus.COMPLETED: set(),
    NodeStatus.FAILED: set(),
    NodeStatus.SKIPPED: set(),
}


class WorkflowEngine:
    def __init__(
        self,
        *,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        multiplier: float = 2.0,
        timeout_seconds: float = 10.0,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.multiplier = multiplier
        self.timeout_seconds = timeout_seconds
        self.sleep = sleep

    async def run(self, run_state: RunState) -> RunState:
        order = validate_and_sort(run_state.graph)
        self._ensure_node_states(run_state)
        self._set_run_status(run_state, "running")
        return await self._run_ordered(run_state, order)

    async def resume(
        self,
        run_state: RunState,
        node_id: str,
        decision: Literal["approved", "rejected"],
    ) -> RunState:
        node_state = run_state.node_states[node_id]
        if node_state.status != NodeStatus.WAITING_FOR_APPROVAL:
            raise InvalidResumeStateError(
                node_id=node_id, status=node_state.status.value
            )

        if decision == "approved":
            existing_output = dict(node_state.output or {})
            self._transition(node_state, NodeStatus.RUNNING)
            self._transition(node_state, NodeStatus.COMPLETED)
            node_state.output = {**existing_output, "decision": "approved"}
            node_state.completed_at = self._now()
            order = validate_and_sort(run_state.graph)
            self._set_run_status(run_state, "running")
            return await self._run_ordered(run_state, order)

        self._transition(node_state, NodeStatus.SKIPPED)
        node_state.error = {"code": "rejected_by_user", "message": "Rejected by user"}
        node_state.completed_at = self._now()
        self._cascade_skip_downstream(run_state, node_id)
        self._set_run_status(run_state, "failed")
        run_state.error = {
            "code": "rejected_by_user",
            "message": "Workflow rejected by user",
        }
        return run_state

    def _transition(
        self, node_state: NodeExecutionState, new_status: NodeStatus
    ) -> None:
        if new_status not in ALLOWED_TRANSITIONS[node_state.status]:
            raise InvalidStateTransitionError(
                from_status=node_state.status.value,
                to_status=new_status.value,
                node_id=node_state.node_id,
            )
        node_state.status = new_status

    async def _run_ordered(self, run_state: RunState, order: list[str]) -> RunState:
        node_by_id = {node.id: node for node in run_state.graph.nodes}
        for node_id in order:
            node_state = run_state.node_states[node_id]
            if node_state.status != NodeStatus.PENDING:
                continue

            node = node_by_id[node_id]
            if self._has_failed_or_skipped_dependency(run_state, node):
                self._transition(node_state, NodeStatus.SKIPPED)
                node_state.completed_at = self._now()
                self._cascade_skip_downstream(run_state, node_id)
                continue

            if not self._dependencies_completed(run_state, node):
                continue

            await self._execute_node(run_state, node, node_state)
            if node_state.status == NodeStatus.WAITING_FOR_APPROVAL:
                self._set_run_status(run_state, "waiting_for_approval")
                return run_state
            if node_state.status == NodeStatus.FAILED:
                self._cascade_skip_downstream(run_state, node_id)

        if any(
            node_state.status == NodeStatus.FAILED
            for node_state in run_state.node_states.values()
        ):
            self._set_run_status(run_state, "failed")
        elif any(
            node_state.status == NodeStatus.WAITING_FOR_APPROVAL
            for node_state in run_state.node_states.values()
        ):
            self._set_run_status(run_state, "waiting_for_approval")
        else:
            self._set_run_status(run_state, "completed")
        return run_state

    async def _execute_node(
        self,
        run_state: RunState,
        node: NodeDefinition,
        node_state: NodeExecutionState,
    ) -> None:
        self._transition(node_state, NodeStatus.RUNNING)
        node_state.started_at = self._now()
        input_payload = resolve_node_inputs(node, run_state)
        node_state.input_snapshot = input_payload
        context = NodeExecutionContext(
            node=node,
            run_state=run_state,
            input_payload=input_payload,
        )

        try:
            handler_cls = get_handler(node.type)
            handler = handler_cls()
            attempt_count = 0

            async def attempt() -> NodeExecutionResult:
                nonlocal attempt_count
                attempt_count += 1
                node_state.retry_count = max(0, attempt_count - 1)
                return await with_timeout(
                    lambda: handler.execute(context),
                    timeout_seconds=self.timeout_seconds,
                )

            retry_kwargs = {
                "max_attempts": self.max_attempts,
                "base_delay": self.base_delay,
                "multiplier": self.multiplier,
                "retryable_exceptions": (TransientError,),
            }
            if self.sleep is not None:
                retry_kwargs["sleep"] = self.sleep
            result = await with_retry(attempt, **retry_kwargs)
        except RetryExhaustedError as exc:
            self._fail_node(
                node_state,
                code="retry_exhausted",
                message=str(exc),
            )
            return
        except PermanentError as exc:
            self._fail_node(
                node_state,
                code="permanent_error",
                message=str(exc),
            )
            return
        except (NodeRegistryError, WorkflowDomainError) as exc:
            self._fail_node(
                node_state,
                code=exc.__class__.__name__,
                message=str(exc),
            )
            return
        except Exception as exc:
            self._fail_node(
                node_state,
                code="node_execution_error",
                message=str(exc),
            )
            return

        if result.status == "completed":
            node_state.output = result.output
            self._transition(node_state, NodeStatus.COMPLETED)
            node_state.completed_at = self._now()
        elif result.status == "failed":
            node_state.error = result.error or {
                "code": "node_failed",
                "message": "Node handler returned failed status",
            }
            self._transition(node_state, NodeStatus.FAILED)
            node_state.completed_at = self._now()
        else:
            node_state.output = result.output
            self._transition(node_state, NodeStatus.WAITING_FOR_APPROVAL)

    def _fail_node(
        self, node_state: NodeExecutionState, *, code: str, message: str
    ) -> None:
        node_state.error = {"code": code, "message": message}
        self._transition(node_state, NodeStatus.FAILED)
        node_state.completed_at = self._now()

    def _cascade_skip_downstream(self, run_state: RunState, node_id: str) -> None:
        dependents = self._dependents_by_node(run_state)
        queue: deque[str] = deque(dependents[node_id])
        while queue:
            downstream_id = queue.popleft()
            downstream_state = run_state.node_states[downstream_id]
            if downstream_state.status == NodeStatus.PENDING:
                self._transition(downstream_state, NodeStatus.SKIPPED)
                downstream_state.completed_at = self._now()
                queue.extend(dependents[downstream_id])

    def _ensure_node_states(self, run_state: RunState) -> None:
        for node in run_state.graph.nodes:
            if node.id not in run_state.node_states:
                run_state.node_states[node.id] = NodeExecutionState(node_id=node.id)

    def _dependencies_completed(
        self, run_state: RunState, node: NodeDefinition
    ) -> bool:
        return all(
            run_state.node_states[dependency].status == NodeStatus.COMPLETED
            for dependency in node.dependencies
        )

    def _has_failed_or_skipped_dependency(
        self, run_state: RunState, node: NodeDefinition
    ) -> bool:
        return any(
            run_state.node_states[dependency].status
            in {NodeStatus.FAILED, NodeStatus.SKIPPED}
            for dependency in node.dependencies
        )

    def _dependents_by_node(self, run_state: RunState) -> dict[str, list[str]]:
        dependents = {node.id: [] for node in run_state.graph.nodes}
        for node in run_state.graph.nodes:
            for dependency in node.dependencies:
                dependents[dependency].append(node.id)
        return dependents

    def _set_run_status(
        self,
        run_state: RunState,
        new_status: Literal[
            "pending", "running", "completed", "failed", "waiting_for_approval"
        ],
    ) -> None:
        object.__setattr__(run_state, "status", new_status)

    def _now(self) -> datetime:
        return datetime.now(UTC)


_DEFAULT_ENGINE = WorkflowEngine()


async def run(run_state: RunState) -> RunState:
    return await _DEFAULT_ENGINE.run(run_state)


async def resume(
    run_state: RunState,
    node_id: str,
    decision: Literal["approved", "rejected"],
) -> RunState:
    return await _DEFAULT_ENGINE.resume(
        run_state=run_state,
        node_id=node_id,
        decision=decision,
    )
