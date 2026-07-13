# Workflow JSON Spec

FlowPilot workflows are directed acyclic graphs of typed nodes. The current MVP uses a linear GitHub Repository Audit graph, but the graph model supports dependencies between nodes.

## Top-Level Shape

```json
{
  "nodes": [
    {
      "id": "manual_trigger",
      "type": "manual_trigger",
      "name": "Manual Trigger",
      "config": {},
      "dependencies": []
    }
  ]
}
```

## Node Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Unique within the workflow. |
| `type` | string | yes | Must match a registered node handler. |
| `name` | string | yes | Human-readable node name. |
| `config` | object | yes | Static node configuration. Defaults to `{}`. |
| `dependencies` | string array | yes | Upstream node ids that must complete first. |

## Validation Rules

- Node ids must be unique.
- Dependencies must reference existing node ids.
- Cycles are rejected.
- Topological order is deterministic.
- Unsafe write nodes such as `github_issue_creator` must be gated by `human_approval`.

## Registered Node Types

| Type | Purpose |
|---|---|
| `manual_trigger` | Captures prompt and repository URL. |
| `github_repo_reader` | Reads repository snapshot through the GitHub client. |
| `ai_repo_analyzer` | Produces audit findings and risk flags. |
| `readme_reviewer` | Scores README quality and suggests improvements. |
| `issue_draft_generator` | Drafts GitHub issues from warning/critical findings. |
| `human_approval` | Pauses execution before risky actions. |
| `github_issue_creator` | Creates or simulates GitHub issues after approval. |
| `linkedin_draft_generator` | Generates a LinkedIn post draft. |
| `markdown_report_writer` | Emits markdown artifacts. |
| `condition` | Safely evaluates simple branch expressions. |

## MVP Graph

The primary graph is linear:

```text
manual_trigger
  -> github_repo_reader
  -> ai_repo_analyzer
  -> readme_reviewer
  -> issue_draft_generator
  -> human_approval
  -> github_issue_creator
  -> linkedin_draft_generator
  -> markdown_report_writer
```

See `examples/github_repo_audit_workflow.json` for a full example.

## Runtime Node Outputs

Node outputs are dictionaries. They are preserved in `run.node_outputs` and summarized into UI-friendly `run.node_results`.

Examples:

- `github_repo_reader`: `repo_snapshot`, `mode`
- `ai_repo_analyzer`: `analysis`, `findings`, `risk_flags`, `summary`
- `issue_draft_generator`: `issue_drafts`
- `human_approval`: `approval_summary`, `issue_drafts`, `risk_level`, `target_repository`
- `github_issue_creator`: `created_issues`, `mode`, `mock`
- `markdown_report_writer`: `artifacts`

## Display Metadata

The backend computes display metadata rather than requiring the frontend to infer labels from raw internals:

- `summary`
- `node_display`
- `layout`
- run `nodes[].display`
- run `timeline`
- run `ui_state`
