# FlowPilot MCP Architecture

## Phase 0

The current codebase establishes the target folder layout and runnable service shells.

```mermaid
flowchart LR
  Browser["Browser"] --> Frontend["Next.js app shell"]
  Frontend --> Backend["FastAPI /api/v1/health"]
  Backend --> Postgres["PostgreSQL"]
  Backend --> Storage["Storage repositories / ports"]
  Storage --> Postgres
  Storage --> Domain["Framework-independent workflow domain"]
  Domain --> State["Serializable RunState"]
  Backend -. future .-> Agents["OpenAI Agents SDK"]
  Backend -. future .-> MCP["MCP registry"]
```

## Design Decisions

- Health returns `not_configured` for OpenAI when no API key is present. This keeps local development bootable while making the missing integration explicit.
- Later workflow logic will live under `backend/app/workflow/` without FastAPI, database, or transport dependencies.
- Persistence is attached outside the domain core through repository ports in `backend/app/storage/ports.py`. SQLAlchemy implementations live under `backend/app/storage/repositories/`, and `backend/app/workflow/` remains free of SQLAlchemy, FastAPI, HTTP, MCP, and agent imports.
- Node execution input snapshots are defined by `resolve_node_inputs`: static node config plus a reserved `_dependencies` map of upstream outputs. This is the contract Phase 2 persists as `input_snapshot_json`.
