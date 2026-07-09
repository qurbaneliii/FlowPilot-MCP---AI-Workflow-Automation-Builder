import ast
from pathlib import Path

WORKFLOW_ROOT = Path(__file__).resolve().parents[2] / "app" / "workflow"


def workflow_imports() -> list[tuple[Path, str]]:
    imports: list[tuple[Path, str]] = []
    for path in WORKFLOW_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend((path, alias.name) for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append((path, node.module))
    return imports


def assert_no_import_prefix(prefixes: tuple[str, ...]) -> None:
    offenders = [
        (path, module)
        for path, module in workflow_imports()
        if any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in prefixes
        )
    ]
    assert offenders == []


def test_workflow_package_has_no_fastapi_import() -> None:
    assert_no_import_prefix(("fastapi",))


def test_workflow_package_has_no_sqlalchemy_import() -> None:
    assert_no_import_prefix(("sqlalchemy",))


def test_workflow_package_has_no_infrastructure_layer_import() -> None:
    assert_no_import_prefix(("httpx", "app.api", "app.mcp", "app.agents"))


def test_node_status_assignment_only_occurs_inside_transition_method() -> None:
    engine_path = WORKFLOW_ROOT / "engine.py"
    tree = ast.parse(engine_path.read_text(encoding="utf-8"))
    offenders: list[int] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Attribute) and target.attr == "status":
                parent = _nearest_function_name(tree, target.lineno)
                if parent != "_transition":
                    offenders.append(target.lineno)

    assert offenders == []


def _nearest_function_name(tree: ast.AST, line_number: int) -> str | None:
    candidates: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.lineno <= line_number <= getattr(node, "end_lineno", node.lineno):
                candidates.append(
                    (node.lineno, getattr(node, "end_lineno", node.lineno), node.name)
                )
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[2]
