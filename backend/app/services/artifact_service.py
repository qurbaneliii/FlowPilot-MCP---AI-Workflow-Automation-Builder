import json
from datetime import datetime
from typing import Any

from app.schemas.run import ArtifactResponse
from app.services.store import STORE, new_id, now
from app.storage.records import ArtifactRecord
from app.workflow.state import RunState


class ArtifactService:
    async def persist_from_run(self, run_state: RunState) -> list[ArtifactResponse]:
        persisted: list[ArtifactResponse] = []
        seen_filenames = {
            _artifact_filename(record)
            for record in STORE.artifacts.get(run_state.run_id, [])
        }
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
                record = ArtifactRecord(
                    id=artifact_id,
                    run_id=run_state.run_id,
                    type=str(payload.get("artifact_type") or "markdown"),
                    content_markdown=json.dumps(payload),
                    created_at=_coerce_datetime(payload["created_at"]),
                )
                STORE.artifacts.setdefault(run_state.run_id, []).append(record)
                persisted.append(_to_response(record))
                seen_filenames.add(filename)
        return persisted

    async def list_for_run(self, run_id: str) -> list[ArtifactResponse]:
        return [_to_response(record) for record in STORE.artifacts.get(run_id, [])]


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
        filename=str(payload.get("filename") or f"{record.type}.md"),
        content=str(payload.get("content") or ""),
        created_at=_coerce_datetime(payload.get("created_at") or record.created_at),
        mode=payload.get("mode"),
        source_node_id=payload.get("source_node_id"),
    )


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
