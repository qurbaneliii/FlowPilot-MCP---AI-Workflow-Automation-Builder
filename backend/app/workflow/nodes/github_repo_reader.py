from typing import Any, ClassVar

from pydantic import BaseModel

from app.mcp.registry import get_client
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
    failed,
    find_repo_url,
    log_node,
    run_controlled,
)


@register_node("github_repo_reader")
class GitHubRepoReaderHandler(NodeHandler):
    input_schema: ClassVar[type[BaseModel]] = EmptyInput
    output_schema: ClassVar[type[BaseModel]] = EmptyOutput

    async def execute(self, context: NodeExecutionContext) -> NodeExecutionResult:
        repo_url = find_repo_url(context)
        if not repo_url:
            return failed("missing_repo_url", "Repository URL is required.")

        async def read_snapshot() -> dict[str, Any]:
            client = get_client("github")
            snapshot = await client.get_repo_snapshot(repo_url)  # type: ignore[attr-defined]
            return _normalize_snapshot(
                snapshot.model_dump(mode="json"), client.mode.value
            )

        result = await run_controlled(
            context,
            read_snapshot,
            failure_code="github_repo_reader_failed",
            failure_message="GitHub repository snapshot could not be read.",
        )
        if isinstance(result, NodeExecutionResult):
            return result
        log_node(
            context,
            "github_repo_reader_completed",
            mode=result.get("mode"),
            file_count=len(result.get("file_tree", [])),
        )
        return completed({"repo_snapshot": result, "mode": result.get("mode")})


def _normalize_snapshot(snapshot: dict[str, Any], mode: str) -> dict[str, Any]:
    file_tree = list(snapshot.get("file_tree") or [])
    readme = snapshot.get("readme")
    package_files = _matching(
        file_tree,
        {
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "setup.py",
            "poetry.lock",
            "pnpm-workspace.yaml",
        },
    )
    lock_files = _suffix_matching(
        file_tree,
        ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock"),
    )
    test_files = [
        path
        for path in file_tree
        if "/test" in path.lower()
        or path.lower().startswith("test")
        or path.lower().endswith(
            ("_test.py", ".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")
        )
    ]
    docs = [path for path in file_tree if path.lower().startswith("docs/")]
    deployment_files = _matching(
        file_tree,
        {"vercel.json", "render.yaml", "railway.json", "fly.toml", "netlify.toml"},
    )
    docker_files = [
        path
        for path in file_tree
        if path.lower().endswith("dockerfile") or "docker-compose" in path.lower()
    ]
    asset_references = [
        path
        for path in file_tree
        if path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"))
        or "screenshot" in path.lower()
    ]
    package_scripts = {}
    metadata = dict(snapshot.get("metadata") or {})
    if isinstance(metadata.get("package_scripts"), dict):
        package_scripts = metadata["package_scripts"]
    return {
        **snapshot,
        "repo_url": str(snapshot.get("repo_url") or ""),
        "metadata": metadata,
        "readme": readme,
        "file_tree": file_tree,
        "package_files": package_files,
        "lock_files": lock_files,
        "test_files": test_files,
        "github_actions_files": _suffix_matching(
            file_tree,
            (
                ".github/workflows/ci.yml",
                ".github/workflows/test.yml",
                ".github/workflows/deploy.yml",
            ),
        ),
        "workflows": list(snapshot.get("workflows") or []),
        "docker_files": docker_files,
        "env_example_present": bool(
            snapshot.get("env_example_present") or ".env.example" in file_tree
        ),
        "gitignore_present": ".gitignore" in file_tree,
        "docs": docs,
        "asset_references": asset_references,
        "deployment_files": deployment_files,
        "package_scripts": package_scripts,
        "mode": mode,
    }


def _matching(paths: list[str], names: set[str]) -> list[str]:
    return [path for path in paths if path.split("/")[-1] in names or path in names]


def _suffix_matching(paths: list[str], suffixes: tuple[str, ...]) -> list[str]:
    return [
        path
        for path in paths
        if path.lower().endswith(tuple(s.lower() for s in suffixes))
    ]
