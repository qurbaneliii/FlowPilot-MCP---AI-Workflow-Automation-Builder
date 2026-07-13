# GitHub Issue Drafts

## Improve README setup instructions

Priority: `medium`

Labels:

- `documentation`
- `priority:medium`

Body:

The README should include a clear setup path for a new evaluator or contributor.

Acceptance criteria:

- Add backend setup commands.
- Add frontend setup commands.
- Document required environment variables.
- Add test and stack verification commands.
- Explain mock versus real behavior.

Mock creation result:

- `mock:https://github.com/example/repo/issues/1`

## Document environment configuration

Priority: `medium`

Labels:

- `documentation`
- `environment`
- `priority:medium`

Body:

The project includes several mode and integration variables, but users need a single reference for safe local development and real integration setup.

Acceptance criteria:

- Explain `OPENAI_AGENT_MODE`.
- Explain `GITHUB_MCP_MODE`.
- Explain `OPENAI_MCP_SERVER_URL`.
- Explain `NEXT_PUBLIC_API_BASE_URL`.
- Warn that real credentials are optional and not used in tests.
