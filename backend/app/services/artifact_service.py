import json
from datetime import datetime
from typing import Any

from app.schemas.run import ArtifactResponse
from app.services.runtime_storage import RuntimeStorage, get_runtime_storage
from app.services.store import STORE, new_id, now
from app.storage.records import ArtifactRecord
from app.workflow.state import RunState


class ArtifactService:
    def __init__(self, storage: RuntimeStorage | None = None) -> None:
        self.storage = storage or get_runtime_storage()

    async def persist_from_run(self, run_state: RunState) -> list[ArtifactResponse]:
        persisted: list[ArtifactResponse] = []
        existing_records = await self.storage.list_artifact_records(run_state.run_id)
        seen_filenames = {_artifact_filename(record) for record in existing_records}
        for node_state in run_state.node_states.values():
            output = node_state.output or {}
            for artifact in (
                output.get("artifacts", []) if isinstance(output, dict) else []
            ):
                if not isinstance(artifact, dict):
                    continue
                filename = str(artifact.get("filename") or "")
                if filename in seen_filenames:
                    continue
                artifact_id = str(artifact.get("artifact_id") or new_id())
                payload = {
                    **artifact,
                    "artifact_id": artifact_id,
                    "run_id": run_state.run_id,
                    "created_at": artifact.get("created_at") or now().isoformat(),
                }
                payload = _enrich_completed_artifact(payload, run_state)
                record = ArtifactRecord(
                    id=artifact_id,
                    run_id=run_state.run_id,
                    type=str(payload.get("artifact_type") or "markdown"),
                    content_markdown=json.dumps(payload),
                    created_at=_coerce_datetime(payload["created_at"]),
                )
                if self.storage.mode == "memory":
                    STORE.artifacts.setdefault(run_state.run_id, []).append(record)
                else:
                    await self.storage.save_artifact(
                        run_state.run_id, record.type, record.content_markdown
                    )
                persisted.append(_to_response(record))
                seen_filenames.add(filename)
        return persisted

    async def list_for_run(self, run_id: str) -> list[ArtifactResponse]:
        records = await self.storage.list_artifact_records(run_id)
        return [_to_response(record) for record in records]


def _artifact_filename(record: ArtifactRecord) -> str:
    try:
        return str(json.loads(record.content_markdown).get("filename") or "")
    except json.JSONDecodeError:
        return ""


def _to_response(record: ArtifactRecord) -> ArtifactResponse:
    payload: dict[str, Any]
    try:
        payload = json.loads(record.content_markdown)
    except json.JSONDecodeError:
        payload = {
            "artifact_id": record.id,
            "run_id": record.run_id,
            "artifact_type": record.type,
            "filename": f"{record.type}.md",
            "content": record.content_markdown,
            "created_at": record.created_at,
        }
    return ArtifactResponse(
        artifact_id=str(payload.get("artifact_id") or record.id),
        run_id=record.run_id,
        artifact_type=str(payload.get("artifact_type") or record.type),
        type=str(payload.get("artifact_type") or record.type),
        filename=str(payload.get("filename") or f"{record.type}.md"),
        title=_artifact_title(str(payload.get("artifact_type") or record.type)),
        content=str(payload.get("content") or ""),
        created_at=_coerce_datetime(payload.get("created_at") or record.created_at),
        mode=payload.get("mode"),
        source_node_id=payload.get("source_node_id"),
        display=_artifact_display(str(payload.get("artifact_type") or record.type)),
    )


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _artifact_title(artifact_type: str) -> str:
    return {
        "repo_audit_report": "Repository audit report",
        "readme_improvement_plan": "README improvement plan",
        "github_issue_drafts": "GitHub issue drafts",
        "linkedin_post_draft": "LinkedIn demo post",
    }.get(artifact_type, artifact_type.replace("_", " ").title())


def _artifact_display(artifact_type: str) -> dict[str, Any]:
    tab = {
        "repo_audit_report": "audit",
        "readme_improvement_plan": "readme",
        "github_issue_drafts": "issues",
        "linkedin_post_draft": "linkedin",
    }.get(artifact_type, "reports")
    badge = (
        "Draft, not published"
        if artifact_type == "linkedin_post_draft"
        else "Generated artifact"
    )
    return {"tab": tab, "empty": False, "copyable": True, "badge": badge}


def _enrich_completed_artifact(
    payload: dict[str, Any], run_state: RunState
) -> dict[str, Any]:
    """Add write results that become available after the report node runs.

    The report intentionally does not depend on the risky write node so rejection
    can still produce safe reports. On approved runs the engine may therefore
    finish the report before issue creation; persistence reconciles the final
    issue URLs into the user-facing artifacts.
    """
    created_issues: list[dict[str, Any]] = []
    for node_state in run_state.node_states.values():
        output = node_state.output or {}
        values = output.get("created_issues")
        if isinstance(values, list):
            created_issues.extend(item for item in values if isinstance(item, dict))
    if not created_issues:
        return payload
    content = str(payload.get("content") or "")
    artifact_type = str(payload.get("artifact_type") or "")
    if artifact_type == "repo_audit_report":
        lines = [
            (
                f"Created issues: {len(created_issues)}"
                if line.startswith("Created issues:")
                else line
            )
            for line in content.splitlines()
        ]
        payload["content"] = "\n".join(lines)
    elif (
        artifact_type == "github_issue_drafts" and "## Creation Results" not in content
    ):
        lines = [content.rstrip(), "", "## Creation Results", ""]
        lines.extend(
            f"- {issue.get('title', 'Untitled')}: {issue.get('display_url') or issue.get('url', '')}"
            for issue in created_issues
        )
        payload["content"] = "\n".join(lines)
    return payload
