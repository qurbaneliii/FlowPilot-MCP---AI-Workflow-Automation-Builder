# Data Model

FlowPilot MCP uses PostgreSQL with SQLAlchemy 2.0 async ORM and Alembic migrations.

## `workflows`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Required, indexed |
| `name` | TEXT | Nullable display name |
| `source_prompt` | TEXT | Required original prompt |
| `graph_json` | JSONB | Required serialized `WorkflowGraph` |
| `created_at` | TIMESTAMPTZ | Required, defaults to `now()` |
| `updated_at` | TIMESTAMPTZ | Required, defaults to `now()` |

## `runs`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `workflow_id` | UUID | Required FK to `workflows.id`, indexed, cascade delete |
| `user_id` | UUID | Required, indexed |
| `status` | TEXT | Required run status |
| `version` | INTEGER | Required optimistic concurrency version, starts at 1 |
| `started_at` | TIMESTAMPTZ | Required, defaults to `now()` |
| `completed_at` | TIMESTAMPTZ | Nullable |
| `error_summary` | TEXT | Nullable human-readable run error summary |

## `node_executions`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `run_id` | UUID | Required FK to `runs.id`, indexed, cascade delete |
| `node_id` | TEXT | Required graph-local id |
| `node_type` | TEXT | Required registered node type |
| `status` | TEXT | Required node status |
| `input_snapshot_json` | JSONB | Nullable resolved input payload |
| `output_json` | JSONB | Nullable node output |
| `logs` | JSONB | Required, defaults to `[]` |
| `error_json` | JSONB | Nullable structured error |
| `started_at` | TIMESTAMPTZ | Nullable |
| `completed_at` | TIMESTAMPTZ | Nullable |
| `retry_count` | INTEGER | Required, defaults to 0 |

Unique constraint: `(run_id, node_id)`.

## `approvals`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `run_id` | UUID | Required FK to `runs.id`, indexed, cascade delete |
| `node_execution_id` | UUID | Required FK to `node_executions.id`, cascade delete |
| `status` | TEXT | Required, defaults to `pending` |
| `requested_at` | TIMESTAMPTZ | Required, defaults to `now()` |
| `resolved_at` | TIMESTAMPTZ | Nullable |
| `resolved_by` | UUID | Nullable future auth field |
| `reason` | TEXT | Nullable rejection or resolution note |

Approval resolution uses `SELECT ... FOR UPDATE` in the repository implementation.

## `artifacts`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `run_id` | UUID | Required FK to `runs.id`, indexed, cascade delete |
| `type` | TEXT | Required artifact type |
| `content_markdown` | TEXT | Required markdown body |
| `created_at` | TIMESTAMPTZ | Required, defaults to `now()` |

Artifacts are scoped to a user through their `run_id -> runs.user_id` chain.

## Deviation Notes

No intentional deviations from the Phase 2 schema specification are present. Tables that do not carry `user_id` directly are scoped through their required parent run/workflow relationship.
