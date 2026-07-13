from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, ValidationError

from app.agents.errors import AgentError
from app.mcp.exceptions import MCPClientError
from app.workflow.exceptions import (
    RetryExhaustedError,
    TransientError,
    WorkflowDomainError,
)
from app.workflow.nodes.base import NodeExecutionContext, NodeExecutionResult
from app.workflow.utils.retry import with_retry
from app.workflow.utils.timeout import with_timeout


T = TypeVar("T")

logger = logging.getLogger(__name__)


class EmptyInput(BaseModel):
    model_config = ConfigDict(extra="allow")


class EmptyOutput(BaseModel):
    model_config = ConfigDict(extra="allow")


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


async def run_controlled(
    context: NodeExecutionContext,
    operation: Callable[[], Awaitable[T]],
    *,
    failure_code: str,
    failure_message: str,
    failure_severity: str | None = None,
    failure_retryable: bool | None = None,
    timeout_seconds: float = 10.0,
    max_attempts: int = 2,
) -> T | NodeExecutionResult:
    try:
        return await with_retry(
            lambda: with_timeout(operation, timeout_seconds=timeout_seconds),
            max_attempts=max_attempts,
            base_delay=0,
            retryable_exceptions=(TransientError,),
        )
    except RetryExhaustedError:
        log_node(
            context,
            "node_retry_exhausted",
            level=logging.WARNING,
            failure_code=failure_code,
        )
        return failed(
            failure_code,
            failure_message,
            severity=failure_severity,
            retryable=failure_retryable,
        )
    except AgentError:
        log_node(
            context,
            "node_agent_failure",
            level=logging.WARNING,
            failure_code=failure_code,
        )
        return failed(
            failure_code,
            failure_message,
            severity=failure_severity,
            retryable=failure_retryable,
        )
    except MCPClientError:
        log_node(
            context,
            "node_mcp_failure",
            level=logging.WARNING,
            failure_code=failure_code,
        )
        return failed(
            failure_code,
            failure_message,
            severity=failure_severity,
            retryable=failure_retryable,
        )
    except (ValidationError, WorkflowDomainError):
        log_node(
            context,
            "node_validation_failure",
            level=logging.WARNING,
            failure_code=failure_code,
        )
        return failed(
            failure_code,
            failure_message,
            severity=failure_severity,
            retryable=failure_retryable,
        )
    except Exception:
        log_node(
            context,
            "node_unexpected_failure",
            level=logging.WARNING,
            failure_code=failure_code,
        )
        return failed(
            failure_code,
            failure_message,
            severity=failure_severity,
            retryable=failure_retryable,
        )


def completed(output: dict[str, Any]) -> NodeExecutionResult:
    return NodeExecutionResult(status="completed", output=output)


def failed(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    *,
    severity: str | None = None,
    retryable: bool | None = None,
) -> NodeExecutionResult:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "details": details or {},
    }
    if severity is not None:
        error["severity"] = severity
    if retryable is not None:
        error["retryable"] = retryable
    return NodeExecutionResult(
        status="failed",
        error=error,
    )


def dependency_outputs(context: NodeExecutionContext) -> dict[str, dict[str, Any]]:
    raw = context.inputs.get("_dependencies", {})
    if not isinstance(raw, dict):
        return {}
    return {key: value for key, value in raw.items() if isinstance(value, dict)}


def first_dependency_value(context: NodeExecutionContext, *keys: str) -> Any:
    for output in dependency_outputs(context).values():
        for key in keys:
            if key in output:
                return output[key]
    return None


def collect_dependency_values(context: NodeExecutionContext, key: str) -> list[Any]:
    values: list[Any] = []
    for output in dependency_outputs(context).values():
        value = output.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            values.extend(value)
        else:
            values.append(value)
    return values


def find_repo_url(context: NodeExecutionContext) -> str | None:
    value = context.inputs.get("repo_url")
    if isinstance(value, str) and value:
        return value
    for key in ("repo_url", "target_repository"):
        value = first_dependency_value(context, key)
        if isinstance(value, str) and value:
            return value
    snapshot = first_dependency_value(context, "repo_snapshot")
    if isinstance(snapshot, dict):
        value = snapshot.get("repo_url")
        if isinstance(value, str) and value:
            return value
    for node_state in context.run_state.node_states.values():
        output = node_state.output or {}
        value = output.get("repo_url") if isinstance(output, dict) else None
        if isinstance(value, str) and value:
            return value
        snapshot = output.get("repo_snapshot") if isinstance(output, dict) else None
        if isinstance(snapshot, dict) and isinstance(snapshot.get("repo_url"), str):
            return snapshot["repo_url"]
    return None


def log_node(
    context: NodeExecutionContext,
    event: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    safe_fields = {
        key: value
        for key, value in fields.items()
        if "secret" not in key.lower() and "token" not in key.lower()
    }
    logger.log(
        level,
        "%s node_id=%s node_type=%s run_id=%s fields=%s",
        event,
        context.node.id,
        context.node.type,
        context.run_state.run_id,
        safe_fields,
    )


def make_artifact(
    *,
    run_id: str,
    artifact_type: str,
    filename: str,
    content: str,
    mode: str | None,
    source_node_id: str,
) -> dict[str, Any]:
    return {
        "artifact_id": str(uuid4()),
        "run_id": run_id,
        "artifact_type": artifact_type,
        "filename": filename,
        "content": content,
        "created_at": utc_now_iso(),
        "mode": mode,
        "source_node_id": source_node_id,
    }
