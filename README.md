# FlowPilot MCP

FlowPilot MCP is an AI Workflow Automation Builder: a natural-language-to-executable-workflow engine that will plan, execute, and audit multi-step automations using OpenAI Agents and MCP tool servers.

## Phase 0 Status

This repository currently contains the Phase 0 scaffold only:

- FastAPI backend app factory with `GET /api/v1/health`
- Next.js App Router shell with Tailwind design tokens
- Docker Compose services for backend, frontend, and PostgreSQL
- Required folder structure for the later domain, persistence, MCP, agent, API, and frontend phases
- Environment documentation, including `OPENAI_API_KEY` and `OPENAI_MCP_SERVER_URL`

## What Is Real vs. Mocked

Real in this phase:

- The backend service starts and serves `/api/v1/health`.
- The frontend service starts and renders the first FlowPilot app shell.
- PostgreSQL runs in Docker Compose and is checked by the health endpoint when `DATABASE_URL` is configured.

Not implemented yet:

- Workflow graph generation and execution
- SQLAlchemy models and Alembic migrations
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

Phase 1 implements the framework-independent workflow domain core. Later phases add persistence, MCP clients, agents, node handlers, the full API layer, frontend workflow screens, and final documentation.
