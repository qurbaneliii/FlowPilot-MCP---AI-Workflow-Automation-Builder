import ast
from typing import Any, ClassVar

from pydantic import BaseModel

from app.workflow.node_registry import register_node
from app.workflow.nodes.base import (
    NodeExecutionContext,
    NodeExecutionResult,
    NodeHandler,
)
from app.workflow.nodes.common import (
    EmptyInput,
    EmptyOutput,
    completed,
    dependency_outputs,
    failed,
    log_node,
)


ALLOWED_AST_NODES = (
    ast.Expression,
    ast.Compare,
    ast.BoolOp,
    ast.UnaryOp,
    ast.Name,
    ast.Constant,
    ast.Subscript,
    ast.Load,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.And,
    ast.Or,
    ast.Not,
)


@register_node("condition")
class ConditionHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        expression = str(context.inputs.get("expression") or "")
        if not expression:
            return failed("missing_expression", "Condition expression is required.")
        names = _evaluation_context(context)
        try:
            tree = ast.parse(expression, mode="eval")
            _validate_tree(tree)
            value = _eval_node(tree.body, names)
        except Exception:
            log_node(
                context,
                "condition_unsafe_expression",
                expression_length=len(expression),
            )
            return failed(
                "unsafe_condition_expression", "Condition expression is not allowed."
            )
        branch = "true" if bool(value) else "false"
        log_node(context, "condition_evaluated", branch=branch)
        return completed({"condition_result": bool(value), "branch": branch})


def _evaluation_context(context: NodeExecutionContext) -> dict[str, Any]:
    values = {
        key: value for key, value in context.inputs.items() if not key.startswith("_")
    }
    values["dependencies"] = dependency_outputs(context)
    return values


def _validate_tree(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.UnaryOp) and not isinstance(node.op, ast.Not):
            raise ValueError("unsupported unary op")
        if isinstance(node, ast.JoinedStr):
            raise ValueError("f-strings are not allowed")
        if not isinstance(node, ALLOWED_AST_NODES):
            raise ValueError(f"unsupported node {type(node).__name__}")


def _eval_node(node: ast.AST, names: dict[str, Any]) -> Any:
    if isinstance(node, ast.BoolOp):
        values = [_eval_node(value, names) for value in node.values]
        return all(values) if isinstance(node.op, ast.And) else any(values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _eval_node(node.operand, names)
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, names)
        for operator, comparator in zip(node.ops, node.comparators, strict=True):
            right = _eval_node(comparator, names)
            if not _compare(left, operator, right):
                return False
            left = right
        return True
    if isinstance(node, ast.Name):
        if node.id not in names:
            raise ValueError("unknown name")
        return names[node.id]
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Subscript):
        container = _eval_node(node.value, names)
        key = _eval_node(node.slice, names)
        return container[key]
    raise ValueError("unsupported expression")


def _compare(left: Any, operator: ast.cmpop, right: Any) -> bool:
    if isinstance(operator, ast.Eq):
        return left == right
    if isinstance(operator, ast.NotEq):
        return left != right
    if isinstance(operator, ast.Lt):
        return left < right
    if isinstance(operator, ast.LtE):
        return left <= right
    if isinstance(operator, ast.Gt):
        return left > right
    if isinstance(operator, ast.GtE):
        return left >= right
    if isinstance(operator, ast.In):
        return left in right
    if isinstance(operator, ast.NotIn):
        return left not in right
    raise ValueError("unsupported comparison")
