# FlowPilot MCP

FlowPilot MCP is an AI Workflow Automation Builder: a natural-language-to-executable-workflow engine that will plan, execute, and audit multi-step automations using OpenAI Agents and MCP tool servers.

## Build Status

- Phase 0: complete. The repository scaffold, FastAPI health endpoint, Next.js app shell, Docker Compose stack definition, and stack verification scripts are in place.
- Phase 1: complete. The framework-independent domain core is implemented and tested: graph validation, deterministic topological sort, run/resume execution, retry, timeout, cascading skip, and human-approval pause semantics.
- Phase 2: complete locally. Persistence adds SQLAlchemy models, Alembic migrations, repository ports/implementations, and database-backed run-state round trips. The 10 real-Postgres integration tests pass against a throwaway native PostgreSQL cluster.
- Phase 3: complete locally. The MCP adapter layer provides GitHub, filesystem, and OpenAI MCP clients behind a shared port and registry, with mock/default and OpenAI unavailable modes tested.
- Phase 4: complete locally. The agent abstraction layer is implemented with Planner, Validator, Executor, Repo Analyzer, README Reviewer, Issue Generator, and LinkedIn Draft agents, strict Pydantic outputs, versioned prompts, fake/unavailable/real backend modes, retry/timeout wrapping, and validation reprompt handling.
- Phase 7: complete locally. The Next.js frontend now provides a polished FlowPilot dashboard for workflow generation, React Flow graph inspection, run polling, approval decisions, logs, node outputs, and rendered artifact viewers.
- Phase 7 UI refinement: complete locally. The frontend now uses a staged generate/workspace experience with a dedicated workflow canvas, contextual approval/run panel, and lower tabs for reports, logs, and node results.

Completed pieces:

- FastAPI backend app factory with `GET /api/v1/health`
- Next.js App Router dashboard with Tailwind design tokens and custom React Flow workflow nodes
- Docker Compose services for backend, frontend, and PostgreSQL
- Framework-independent workflow domain core under `backend/app/workflow/`
- Environment documentation, including `OPENAI_API_KEY`, `OPENAI_AGENT_MODE`, `OPENAI_AGENT_MODEL`, and `OPENAI_MCP_SERVER_URL`

## What Is Real vs. Mocked

Real in this phase:

- The backend service starts and serves `/api/v1/health`.
- The frontend service starts and renders the FlowPilot dashboard. It can generate a workflow, start a run, poll status, resolve approvals, and render generated artifacts against the current local API.
- PostgreSQL runs in Docker Compose and is checked by the health endpoint when `DATABASE_URL` is configured.
- Workflow graph validation and execution are real as a standalone in-memory domain module. This includes duplicate/dangling/cycle validation, deterministic topological sort, state transitions, retry/timeout handling, cascading skips, and approval pause/resume. It is currently exercised by test fixtures in `backend/tests/fixtures/fake_node_handlers.py`; it is not yet wired to persistence, the API layer, real node handlers, MCP clients, or agents.
- Persistence models, migrations, repository ports, and SQLAlchemy repository implementations are present. Integration tests are written for real PostgreSQL and run under CI with a Postgres service container; local execution depends on a reachable `TEST_DATABASE_URL` or `DATABASE_URL`.
- MCP adapter clients are real as interface-complete adapters. GitHub and filesystem default to explicit mock mode for safe local development. OpenAI MCP supports `REAL` mode when `OPENAI_MCP_SERVER_URL` and `OPENAI_API_KEY` are configured, and `UNAVAILABLE` mode otherwise. OpenAI MCP protocol behavior is verified against a local fake MCP server, not the public OpenAI service.
- The OpenAI agent layer is real as an interface-complete, testable abstraction. Agent wrappers load versioned prompts, invoke a selected backend mode, validate strict Pydantic outputs, retry transient failures, and reprompt once on invalid model output. Local tests use deterministic fake/unavailable backends; the real OpenAI Agents SDK transport is intentionally isolated and is not exercised by tests.

Not implemented yet:

- Production deployment hardening and real external MCP credential wiring
- Final screenshot capture for `docs/screenshots/` after the stack is running

If `OPENAI_API_KEY` is missing, health reports OpenAI as `not_configured`. If `OPENAI_MCP_SERVER_URL` is missing, the OpenAI MCP client uses explicit unavailable mode rather than silently returning fake tool results.

## Demo Flow

Use the frontend at <http://localhost:3000> for the primary MVP walkthrough:

1. Enter a GitHub repository URL such as `https://github.com/example/repo`.
2. Generate executable workflow.
3. Review the React Flow graph and node inspector.
4. Run workflow and watch the timeline/status panels update.
5. Approve or reject the guarded GitHub issue creation step.
6. Review Repo Audit Report, README Improvement Plan, GitHub Issue Drafts, and LinkedIn Draft in the artifact panel.

Screenshot placeholders live in `docs/screenshots/` so README and portfolio captures have a stable destination.
The active workflow screen prioritizes the canvas first, then shows approval, reports, logs, and node outputs through contextual panels and tabs so demo screenshots stay readable.

## Quickstart

1. Copy `.env.example` to `.env` if you want to set real credentials.
2. Verify the full stack:

```powershell
.\scripts\verify_stack.ps1
```

This is the canonical runtime check. It builds and starts the Docker Compose stack, waits for backend `/api/v1/health` to return `200` with `database: "ok"`, then waits for the frontend root URL to return `200`.

On macOS/Linux or Git Bash, the equivalent script is:

```bash
./scripts/verify_stack.sh
```

3. Open the services:

- Backend health: <http://localhost:8000/api/v1/health>
- Frontend: <http://localhost:3000>

## Roadmap

Phases 1-7 are complete locally for the GitHub Repo Audit MVP path. Later phases can focus on production deployment hardening, real credential walkthroughs, and final screenshot/demo capture.

## Phase Completion Rule

Every phase completion must include README/docs synchronization as part of its Definition of Done, including the current build status, real-vs-mocked behavior, and roadmap updates.
