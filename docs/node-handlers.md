# Node Handlers

Production node handlers live in `backend/app/workflow/nodes/` and register themselves with the workflow node registry.

## Registered Production Handlers

| Node type | File | Behavior |
|---|---|---|
| `manual_trigger` | `manual_trigger.py` | Captures prompt and repo URL. |
| `github_repo_reader` | `github_repo_reader.py` | Reads repository snapshot through GitHub client. |
| `ai_repo_analyzer` | `ai_repo_analyzer.py` | Runs repo analyzer agent. |
| `readme_reviewer` | `readme_reviewer.py` | Runs README reviewer agent. |
| `issue_draft_generator` | `issue_draft_generator.py` | Runs issue generator agent. |
| `human_approval` | `human_approval.py` | Pauses execution and emits approval payload. |
| `github_issue_creator` | `github_issue_creator.py` | Requires approved approval payload before creating issues. |
| `linkedin_draft_generator` | `linkedin_draft_generator.py` | Runs LinkedIn draft agent; never publishes. |
| `markdown_report_writer` | `markdown_report_writer.py` | Emits markdown artifacts. |
| `condition` | `condition.py` | Safely evaluates limited branch expressions. |

## Failure Handling

Shared helpers in `nodes/common.py` convert expected failures into controlled `NodeExecutionResult` objects:

- agent errors
- MCP client errors
- Pydantic validation errors
- workflow domain errors
- retry exhaustion
- timeouts
- unexpected raw exceptions

The UI sees structured node failure data rather than stack traces.

## Approval-Gated Issue Creation

`github_issue_creator` requires an upstream approval output with `decision: "approved"`. Missing, pending, or rejected approval produces controlled failure/skip behavior.

The handler also uses an idempotency key derived from:

- run id
- node id
- issue title

Mock issue creation returns explicit mock display URLs. Real mode requires a token, writes only after approval, and uses an idempotency marker so retries can reuse an existing issue.

## Condition Node Safety

The condition node accepts a restricted expression form. Tests cover rejection of:

- function calls
- attribute access
- imports
- unsafe builtins

Names resolve only from the provided context.

## Test-Only Fake Handlers

`backend/tests/fixtures/fake_node_handlers.py` contains fake handlers for workflow engine tests. They are test-only and are separate from production node handlers.

## Artifacts

`markdown_report_writer` emits:

- `repo_audit_report`
- `readme_improvement_plan`
- `github_issue_drafts`
- `linkedin_post_draft`

Artifacts are persisted by `ArtifactService` and returned with metadata and display hints for the frontend. Persistence reconciles approved issue-creation results into the final report artifacts without making safe report generation depend on the risky write node.
