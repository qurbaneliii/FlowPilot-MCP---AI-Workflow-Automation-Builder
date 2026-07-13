# GitHub Repository Audit Use Case

The MVP use case audits a GitHub repository and prepares review artifacts without performing risky writes until a human approves them.

## User Goal

Given a GitHub repository URL and an audit prompt, FlowPilot should:

- read repository structure and README content
- identify documentation, setup, testing, CI/CD, security hygiene, and portfolio-readiness issues
- draft guarded GitHub issues
- pause before issue creation
- create or simulate issues only after approval
- produce markdown artifacts and a LinkedIn draft

## Workflow

```text
manual_trigger
github_repo_reader
ai_repo_analyzer
readme_reviewer
issue_draft_generator
human_approval
github_issue_creator
linkedin_draft_generator
markdown_report_writer
```

## Node Responsibilities

| Node | Responsibility |
|---|---|
| `manual_trigger` | Stores prompt and repository URL. |
| `github_repo_reader` | Reads mock or real repository snapshot. |
| `ai_repo_analyzer` | Produces findings, risk flags, and summary. |
| `readme_reviewer` | Scores README quality and suggests missing sections. |
| `issue_draft_generator` | Converts warning/critical findings into issue drafts. |
| `human_approval` | Pauses before external GitHub issue creation. |
| `github_issue_creator` | Creates or simulates GitHub issues after approval. |
| `linkedin_draft_generator` | Drafts a professional demo post, never publishes it. |
| `markdown_report_writer` | Emits report artifacts for the UI. |

## Approval Behavior

Before issue creation:

- run status becomes `waiting_for_approval`
- `approval` is returned in the run response
- `github_issue_creator` remains `pending`
- `ui_state.recommended_tab` becomes `approval`

On approve:

- approval status becomes `approved`
- workflow resumes
- issue creator runs in mock or real mode
- report artifacts are generated

On reject:

- approval status becomes `rejected`
- issue creator is skipped
- safe report generation continues when possible

## Artifacts

The completed run should expose:

- `repo_audit_report`
- `readme_improvement_plan`
- `github_issue_drafts`
- `linkedin_post_draft`

The `artifact_tabs` response indicates which tabs are available.

## Mock Mode

The default local path uses a mock GitHub client and fake agents. Mock issue creation returns explicit mock URLs and mode fields, so the UI and examples do not imply real GitHub writes. With `GITHUB_MCP_MODE=real`, the built-in REST adapter can read a public repository without a token; issue writes additionally require a token and the existing human approval gate.

## Example Files

- `examples/github_repo_audit_workflow.json`
- `examples/sample_repo_audit_report.md`
- `examples/sample_readme_improvement_plan.md`
- `examples/sample_issue_drafts.md`
- `examples/sample_linkedin_post.md`
