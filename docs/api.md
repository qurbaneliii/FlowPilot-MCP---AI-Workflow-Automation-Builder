# API

Base URL for local frontend use:

```text
http://127.0.0.1:8000/api/v1
```

All responses are JSON. API errors use the structured error shape shown at the end of this document.

## GET `/health`

Checks process health, database reachability, OpenAI configuration, and UI-friendly service labels.

Example degraded local response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "dependencies": {
    "database": "not_configured",
    "openai": "not_configured"
  },
  "services": {
    "backend": {
      "status": "ok",
      "label": "Backend connected",
      "severity": "success",
      "blocking": false
    },
    "database": {
      "status": "memory",
      "label": "Memory mode",
      "severity": "info",
      "blocking": false
    },
    "mcp": {
      "status": "mock",
      "label": "Mock MCP",
      "severity": "info",
      "blocking": false
    },
    "openai": {
      "status": "not_configured",
      "label": "Fake agent mode",
      "severity": "info",
      "blocking": false
    }
  },
  "ui": {
    "primary_mode_label": "Mock MCP",
    "storage_mode_label": "Memory mode",
    "show_database_warning": true,
    "database_warning_blocks_demo": false
  },
  "storage": {
    "mode": "memory",
    "persistent": false,
    "reset_on_restart": true
  }
}
```

Rules:

- `dependencies` is preserved for older clients.
- `services.*.blocking` tells the frontend whether a warning should be red/error-level.
- Mock/in-memory demo modes are explicit and not presented as catastrophic failures.
- Postgres mode reports `Postgres connected`; an unavailable configured Postgres service is blocking and never silently falls back to memory.

## POST `/workflows/generate`

Generates and validates a GitHub repository audit workflow.

Request:

```json
{
  "prompt": "Audit this GitHub repository and draft guarded improvement issues.",
  "repo_url": "https://github.com/example/repo"
}
```

Response includes:

- `workflow_id`
- `workflow`
- `validation`
- `summary`
- `node_display`
- `layout`
- `warnings`

The `workflow` object follows the spec in `docs/workflow-json-spec.md`.

## GET `/workflows/{workflow_id}`

Returns a persisted workflow graph with source metadata and UI-friendly workflow display fields.

Response includes:

- `workflow_id`
- `workflow`
- `metadata.source_prompt`
- `metadata.repo_url`
- `metadata.created_at`
- `summary`
- `node_display`
- `layout`

## POST `/workflows/run`

Starts a run for a generated workflow.

Request:

```json
{
  "workflow_id": "wf_or_uuid"
}
```

Response:

```json
{
  "run_id": "run_or_uuid",
  "status": "running"
}
```

The run executes as a background task.

## GET `/runs/{run_id}`

Returns the raw run state plus UI-friendly view models.

Important fields:

- `run_id`
- `workflow_id`
- `status`
- `summary`
- `nodes`
- `timeline`
- `approval`
- `logs`
- `node_outputs`
- `node_results`
- `errors`
- `artifacts`
- `artifact_tabs`
- `pending_approval`
- `ui_state`
- `inspector`
- `layout`
- `mode`

Status values:

```text
pending
running
waiting_for_approval
completed
failed
```

Node status values:

```text
pending
running
completed
failed
waiting_for_approval
skipped
```

When the run is waiting for approval:

- `approval` is a first-class panel object
- `pending_approval` remains for backward compatibility
- `ui_state.recommended_tab` is `approval`
- `github_issue_creator` remains `pending`

When the run completes:

- `artifacts` contains report content and metadata
- `artifact_tabs` marks available tabs
- `ui_state.recommended_tab` is `reports`

## GET `/runs`

Lists recent runs.

Query parameters:

- `limit`: integer, default `20`, max `100`
- `offset`: integer, default `0`

Response:

```json
{
  "runs": [],
  "limit": 20,
  "offset": 0
}
```

## POST `/approvals/{approval_id}/approve`

Approves a pending guarded action and resumes execution.

Response includes:

```json
{
  "approval_id": "appr_or_uuid",
  "status": "approved",
  "decision": "approved",
  "run_id": "run_or_uuid",
  "message": "Approval recorded. Workflow will resume.",
  "run_status": "completed",
  "next_poll_recommended": true,
  "run": {}
}
```

Duplicate approval calls are controlled with a structured `409` conflict.

## POST `/approvals/{approval_id}/reject`

Rejects the guarded action. For the MVP, GitHub issue creation is skipped and safe report generation can continue.

Response includes:

```json
{
  "approval_id": "appr_or_uuid",
  "status": "rejected",
  "decision": "rejected",
  "run_id": "run_or_uuid",
  "message": "Approval rejected. GitHub issue creation will be skipped.",
  "run_status": "completed",
  "next_poll_recommended": true,
  "run": {}
}
```

## Structured Errors

Example:

```json
{
  "error": {
    "code": "INVALID_REPO_URL",
    "message": "Repository URL must be a GitHub owner/repo URL.",
    "details": {
      "repo_url": "not-a-url"
    },
    "severity": "warning",
    "retryable": false
  }
}
```

Guidelines:

- Messages should be user-facing.
- Stack traces are not returned.
- Field-level details are included where useful.
- `retryable` helps the frontend decide whether retry UI is appropriate.
