# FlowPilot MCP API

## GET `/api/v1/health`

Returns process health and lightweight dependency status.

Example response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "dependencies": {
    "database": "ok",
    "openai": "not_configured"
  }
}
```

## POST `/api/v1/workflows/generate`

Generates and validates a GitHub repository audit workflow, then persists the graph.

```json
{
  "prompt": "Analyze this GitHub repository and generate issue drafts.",
  "repo_url": "https://github.com/example/repo"
}
```

Returns `workflow_id`, `workflow`, `validation`, and `warnings`.

## GET `/api/v1/workflows/{workflow_id}`

Returns the saved workflow graph and source metadata.

## POST `/api/v1/workflows/run`

Creates a run and starts execution in a background task.

```json
{
  "workflow_id": "..."
}
```

Returns quickly with `{ "run_id": "...", "status": "running" }`.

## GET `/api/v1/runs/{run_id}`

Returns run status, node statuses, node outputs, errors, artifacts, pending approval, and mock/real mode where available.

## GET `/api/v1/runs`

Returns recent runs with `limit` and `offset` pagination.

## POST `/api/v1/approvals/{approval_id}/approve`

Approves a pending risky action and resumes execution. GitHub issue creation remains approval-gated and idempotent.

## POST `/api/v1/approvals/{approval_id}/reject`

Rejects the risky write, skips issue creation, and continues safe report generation when the workflow graph allows it.

## Structured Errors

API errors use this shape:

```json
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow not found.",
    "details": {}
  }
}
```
