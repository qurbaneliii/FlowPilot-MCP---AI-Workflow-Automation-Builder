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
  },
  "services": {
    "backend": {
      "status": "ok",
      "label": "Backend connected",
      "severity": "success",
      "blocking": false
    },
    "database": {
      "status": "not_configured",
      "label": "Memory mode",
      "severity": "warning",
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
  }
}
```

`dependencies` is preserved for older clients. New `services` and `ui` fields distinguish blocking outages from non-blocking local/demo modes, so the frontend only renders red service status when `blocking` is true.

## POST `/api/v1/workflows/generate`

Generates and validates a GitHub repository audit workflow, then persists the graph.

```json
{
  "prompt": "Analyze this GitHub repository and generate issue drafts.",
  "repo_url": "https://github.com/example/repo"
}
```

Returns `workflow_id`, `workflow`, `validation`, `warnings`, and UI-friendly view data:

- `summary`: compact workflow name, repo URL, node count, stage count, risk count, approval requirement, mode, and status label.
- `node_display`: stable display name, subtitle, icon token, order, stage, dependencies, risk level, and description for each node.
- `layout`: optional canvas positioning hints.

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

Returns run status, node statuses, node outputs, errors, artifacts, pending approval, and mock/real mode where available. The raw fields remain available for advanced/debug views.

The response also includes UI-oriented fields:

- `summary`: run card data, counts, active node, timestamps, and `next_required_action`.
- `nodes[].display`: concise node card summary, icon token, severity, and approval/risk flags.
- `timeline`: ordered readable node status messages.
- `approval`: first-class approval panel data when approval is pending; otherwise `null`.
- `artifacts`: artifact metadata, content, title, type, and display hints.
- `artifact_tabs`: availability by stable artifact type, avoiding contradictory empty states.
- `node_results`: human-readable node output summaries with metrics.
- `ui_state`: recommended active tab/view, canvas focus node, panel visibility, and optional banner.

## GET `/api/v1/runs`

Returns recent runs with `limit` and `offset` pagination.

## POST `/api/v1/approvals/{approval_id}/approve`

Approves a pending risky action and resumes execution. The response includes `status`, `run_id`, user-facing `message`, `run_status`, `next_poll_recommended`, and the updated `run`.

## POST `/api/v1/approvals/{approval_id}/reject`

Rejects the risky write, skips issue creation, and continues safe report generation when the workflow graph allows it. The response includes the same frontend action hints as approval.

## Structured Errors

API errors use this shape:

```json
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow not found.",
    "details": {},
    "severity": "warning",
    "retryable": false
  }
}
```
