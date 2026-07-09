# FlowPilot MCP

FlowPilot MCP is an AI Workflow Automation Builder: a natural-language-to-executable-workflow engine that will plan, execute, and audit multi-step automations using OpenAI Agents and MCP tool servers.

## Build Status

- Phase 0: complete. The repository scaffold, FastAPI health endpoint, Next.js app shell, Docker Compose stack definition, and stack verification scripts are in place.
- Phase 1: complete. The framework-independent domain core is implemented and tested: graph validation, deterministic topological sort, run/resume execution, retry, timeout, cascading skip, and human-approval pause semantics.
- Phase 2: in progress. Persistence adds SQLAlchemy models, Alembic migrations, repository ports/implementations, and database-backed run-state round trips.

Completed pieces:

- FastAPI backend app factory with `GET /api/v1/health`
- Next.js App Router shell with Tailwind design tokens
- Docker Compose services for backend, frontend, and PostgreSQL
- Framework-independent workflow domain core under `backend/app/workflow/`
- Environment documentation, including `OPENAI_API_KEY` and `OPENAI_MCP_SERVER_URL`

## What Is Real vs. Mocked

Real in this phase:

- The backend service starts and serves `/api/v1/health`.
- The frontend service starts and renders the first FlowPilot app shell.
- PostgreSQL runs in Docker Compose and is checked by the health endpoint when `DATABASE_URL` is configured.
- Workflow graph validation and execution are real as a standalone in-memory domain module. This includes duplicate/dangling/cycle validation, deterministic topological sort, state transitions, retry/timeout handling, cascading skips, and approval pause/resume. It is currently exercised by test fixtures in `backend/tests/fixtures/fake_node_handlers.py`; it is not yet wired to persistence, the API layer, real node handlers, MCP clients, or agents.
- Persistence models, migrations, repository ports, and SQLAlchemy repository implementations are present. Integration tests are written for real PostgreSQL and run under CI with a Postgres service container; local execution depends on a reachable `TEST_DATABASE_URL` or `DATABASE_URL`.

Not implemented yet:

- MCP clients and registry
- OpenAI Agents SDK wrappers
- Node handlers, approvals, artifact generation, and the full API contract

If `OPENAI_API_KEY` is missing, health reports OpenAI as `not_configured`. If `OPENAI_MCP_SERVER_URL` is missing, the future OpenAI MCP client must use documented no-op mode and log `OPENAI_MCP_NOT_CONFIGURED`.

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

Phase 1 is complete. Phase 2 persistence is the current focus. Later phases add MCP clients, agents, real node handlers, the full API layer, frontend workflow screens, and final documentation.

## Phase Completion Rule

Every phase completion must include README/docs synchronization as part of its Definition of Done, including the current build status, real-vs-mocked behavior, and roadmap updates.
