# Agent Layer

The agent layer wraps AI transformations behind a testable interface. It supports fake, unavailable, and real backends without changing node handler code.

## Agents

Seven agents exist:

| Agent | Purpose | Output schema |
|---|---|---|
| Planner | Converts prompt/repo URL into a workflow graph. | `WorkflowGraph` |
| Validator | Validates and optionally corrects workflow graphs. | `ValidatorOutput` |
| Executor | Generic structured execution result adapter. | `ExecutorOutput` |
| Repo Analyzer | Produces audit findings, risk flags, and summary. | `RepoAnalyzerOutput` |
| README Reviewer | Scores README quality and suggests sections. | `ReadmeReviewerOutput` |
| Issue Generator | Drafts GitHub issues from findings. | `IssueGeneratorOutput` |
| LinkedIn Draft Generator | Drafts a LinkedIn post. | `LinkedInDraftOutput` |

## Agent Runner

`AgentRunner` handles:

- loading versioned prompts from `backend/app/agents/prompts/<agent>/v1.md`
- selecting backend mode from settings
- invoking the backend with timeout and retry
- validating Pydantic output
- reprompting exactly once after invalid output
- failing clearly after a second invalid output

## Backend Modes

```text
OPENAI_AGENT_MODE=fake
OPENAI_AGENT_MODE=unavailable
OPENAI_AGENT_MODE=real
```

### Fake

Deterministic fake outputs for local development and tests.

### Unavailable

Fails clearly when an agent is invoked.

### Real

Uses the OpenAI-backed adapter and requires:

```text
OPENAI_API_KEY=...
OPENAI_AGENT_MODEL=gpt-4.1
```

Tests do not call the real OpenAI API.

## Schema Validation

Agent schemas reject unexpected fields and invalid enums. Examples:

- finding categories must be known categories
- README score must be `0..100`
- issue priority must be `low`, `medium`, or `high`
- LinkedIn draft text must not claim it was posted or auto-published

## Prompt Safety

Prompts are versioned and tested to ensure they are not placeholders. The planner and validator are responsible for preserving approval gates before risky writes.

## Test Coverage

The suite covers:

- not-configured failures
- valid first response
- one reprompt on invalid output
- failure after second invalid output
- transient retry
- permanent error handling
- planner registry awareness
- validator deterministic graph checks
- unsafe write detection
- schema enforcement
