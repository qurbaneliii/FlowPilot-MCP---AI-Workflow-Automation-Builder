# FlowPilot MCP

Lightweight AI workflow automation engine for turning natural-language automation requests into executable, auditable workflow graphs.

FlowPilot MCP converts a user request into a typed workflow graph, executes the graph through OpenAI-style agent abstractions and MCP-style tool clients, persists run state and artifacts, and requires human approval before risky actions such as GitHub issue creation. The MVP is focused on a GitHub Repository Audit workflow that reads a repository snapshot, analyzes documentation and project readiness, drafts guarded issues, generates a LinkedIn demo draft, and writes markdown reports.

This is not just a chatbot. FlowPilot separates planning, validation, execution, tool access, state transitions, approval gates, and generated artifacts. The frontend renders the workflow as a runbook-style product surface with node status, timeline, approval panel, reports, logs, and raw debug details.

## Core MVP Demo Flow

1. Enter a prompt and GitHub repository URL.
2. Generate a validated workflow graph.
3. Inspect the React Flow canvas, node metadata, and workflow summary.
4. Start a run.
5. Watch node statuses and timeline entries update.
6. Review the human approval panel before GitHub issue creation.
7. Approve or reject the guarded action.
8. Review generated artifacts:
   - Repository audit report
   - README improvement plan
   - GitHub issue drafts
   - LinkedIn post draft

## Architecture Overview

FlowPilot keeps the workflow engine independent from FastAPI, database, agents, and MCP clients. API services coordinate graph generation, execution, approvals, artifacts, and UI-friendly response views.

```mermaid
flowchart LR
  User["User"] --> Frontend["Next.js Frontend"]
  Frontend --> API["FastAPI API"]
  API --> Generation["Workflow Generation Service"]
  API --> RunService["Workflow Run Service"]
  API --> Query["Run Query / View Services"]
  Generation --> Planner["Planner Agent"]
  Generation --> Validator["Validator Agent"]
  RunService --> Engine["Pure Workflow Engine"]
  Engine --> Nodes["Registered Node Handlers"]
  Nodes --> Agents["Agent Runner"]
  Nodes --> MCP["MCP-style Tool Clients"]
  Query --> UI["UI-friendly summaries"]
  RunService --> Store["In-memory MVP Store"]
  Store -.future.-> Postgres["SQLAlchemy/PostgreSQL layer"]
  Agents --> Fake["Fake backend"]
  Agents --> OpenAI["Real OpenAI backend"]
  MCP --> GitHub["GitHub mock/real client"]
  MCP --> FS["Filesystem mock/real client"]
  MCP --> OpenAIMCP["OpenAI MCP unavailable/real client"]
```

## Tech Stack

- Backend: FastAPI, Pydantic v2, SQLAlchemy async models, Alembic, pytest, Ruff, Black
- Workflow engine: pure Python graph validation, deterministic topological execution, retry/timeout, approval pause/resume
- Agents: planner, validator, executor, repo analyzer, README reviewer, issue generator, LinkedIn draft generator
- MCP-style tools: GitHub, filesystem, and OpenAI MCP client ports with explicit mock/real/unavailable modes
- Frontend: Next.js App Router, React 19, TypeScript, Tailwind CSS, React Flow, lucide-react
- Dev/runtime: Docker Compose with PostgreSQL, backend, and frontend services

## Folder Structure

```text
backend/
  app/
    agents/          Agent abstractions, prompts, fake/real/unavailable backends
    api/v1/          FastAPI routers
    core/            config, logging, structured API errors
    mcp/             MCP-style client ports, registry, concrete/mock clients
    schemas/         API response/request schemas
    services/        generation, run, approval, artifact, query/view services
    storage/         repository ports and SQLAlchemy repository implementations
    workflow/        pure graph, engine, state, node registry, node handlers
  tests/             unit and integration coverage
docs/                practical architecture, API, UX, MCP, agent, and test docs
examples/            sample workflow graph and generated artifacts
frontend/
  src/
    app/             Next.js routes
    components/      workflow, run, approval, report, and layout UI
    hooks/           workflow/run/approval client hooks
    lib/             API client and workflow mapping helpers
    types/           TypeScript API and product types
scripts/             stack verification and markdown fence checks
```

## Backend API Endpoints

- `GET /api/v1/health`: process health, dependency status, UI-friendly service labels, and blocking flags.
- `POST /api/v1/workflows/generate`: generate, validate, persist, summarize, and display-map a workflow.
- `GET /api/v1/workflows/{workflow_id}`: retrieve a saved workflow graph and metadata.
- `POST /api/v1/workflows/run`: create a run and execute it in the background.
- `GET /api/v1/runs/{run_id}`: retrieve run state, node status, timeline, approval panel data, artifacts, logs, raw outputs, and `ui_state`.
- `GET /api/v1/runs`: list recent runs.
- `POST /api/v1/approvals/{approval_id}/approve`: record approval, resume execution, and return frontend action hints.
- `POST /api/v1/approvals/{approval_id}/reject`: reject the risky write, skip gated issue creation, and return frontend action hints.

## Frontend Product Flow

The frontend is a workflow workspace, not a chat transcript:

- Start view: prompt, repository URL, example prompts, validation/error states.
- Summary bar: backend-provided workflow summary, mode, risk count, approval requirement.
- Canvas: custom React Flow nodes with backend display metadata and run status.
- Context panel: run summary, selected node inspector, approval card, or completion summary.
- Lower workspace tabs: overview, approval, reports, logs, node results.
- Reports: artifact tabs use backend availability metadata to avoid contradictory empty states.

## GitHub Repo Audit Use Case

The MVP graph performs this linear audit:

1. `manual_trigger`
2. `github_repo_reader`
3. `ai_repo_analyzer`
4. `readme_reviewer`
5. `issue_draft_generator`
6. `human_approval`
7. `github_issue_creator`
8. `linkedin_draft_generator`
9. `markdown_report_writer`

The `condition` node handler also exists and is tested, but it is optional for this MVP graph.

## Human Approval Behavior

GitHub issue creation is approval-gated. The run pauses at `human_approval`, creates a pending approval record, and leaves `github_issue_creator` pending. Approving resumes the run and allows issue creation in mock or real mode. Rejecting skips the issue creator and continues safe report generation when the graph allows it. Duplicate approval calls return a structured conflict.

## Agent Layer

Seven agents exist behind a shared `AgentRunner`:

- Planner
- Validator
- Executor
- Repo Analyzer
- README Reviewer
- Issue Generator
- LinkedIn Draft Generator

Agent outputs are schema-validated with Pydantic. Invalid output is reprompted exactly once. Fake mode provides deterministic tests. Unavailable mode fails clearly. Tests do not call the real OpenAI API.

## MCP Integration

MCP-style clients sit behind ports and a registry:

- GitHub client: mock by default, real mode when configured.
- Filesystem client: mock by default, real mode limited to `FILESYSTEM_MCP_ROOT`.
- OpenAI MCP client: unavailable when no server URL is configured, real when configured.

Mock mode is explicit in outputs and UI labels. The project does not claim full production MCP connectivity by default.

## Mock vs Real Behavior

Default local behavior is intentionally safe:

- `OPENAI_AGENT_MODE=fake` uses deterministic fake agent outputs.
- `GITHUB_MCP_MODE=mock` simulates repository reads and issue creation.
- Database may show non-blocking `Memory mode` outside Docker.
- Docker Compose starts PostgreSQL and expects health to report `database: "ok"`.

Real OpenAI/GitHub/MCP execution requires explicit credentials and mode changes. Production hardening is not complete.

## Setup

```powershell
git clone <repo-url>
cd "FlowPilot MCP - AI Workflow Automation Builder"
Copy-Item .env.example .env
```

Install backend dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Install frontend dependencies:

```powershell
cd frontend
npm install
```

## Environment Variables

Core variables:

```text
APP_ENV=development
APP_VERSION=0.1.0
DATABASE_URL=postgresql+asyncpg://flowpilot:flowpilot@localhost:5432/flowpilot
OPENAI_AGENT_MODE=fake
OPENAI_AGENT_MODEL=gpt-4.1
OPENAI_API_KEY=
OPENAI_MCP_SERVER_URL=
GITHUB_MCP_MODE=mock
GITHUB_MCP_SERVER_URL=
GITHUB_TOKEN=
FILESYSTEM_MCP_MODE=mock
FILESYSTEM_MCP_ROOT=/workspace
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Run Backend

```powershell
cd backend
$env:PYTHONPATH='.'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

## Run Frontend

```powershell
cd frontend
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open <http://127.0.0.1:3000>.

## Run Tests

Backend:

```powershell
cd backend
$env:PYTHONPATH='.'
pytest
ruff check app tests
black --check app tests alembic ..\scripts\check_markdown_fences.py
```

Frontend:

```powershell
cd frontend
npm run typecheck
npm run lint
npm run build
```

## Verify Stack

With Docker running:

```powershell
docker info
docker compose config --quiet
.\scripts\verify_stack.ps1
```

On macOS/Linux or Git Bash:

```bash
docker info
docker compose config --quiet
./scripts/verify_stack.sh
```

The verification script builds and starts PostgreSQL, backend, and frontend, waits for backend health with `database: "ok"`, then checks the frontend root returns HTTP 200.

## Known Limitations

- The API MVP uses in-process store state for workflow/run/query services; SQLAlchemy repositories and migrations exist but are not the primary API runtime path yet.
- Real OpenAI and external MCP/GitHub credentials are optional and not exercised in tests.
- Browser screenshot/GIF assets are placeholders until a final recorded demo is captured.
- Authentication, multi-user tenancy, deployment hardening, queueing, and background worker isolation are future work.
- The project is focused on a lightweight, auditable AI workflow MVP rather than a broad no-code automation suite.

## Roadmap

- Wire API runtime to durable PostgreSQL repositories.
- Add authenticated project/user scopes.
- Expand workflow templates beyond GitHub repository audit.
- Add production-ready background execution and resumability.
- Add real MCP credential walkthroughs.
- Capture final screenshots and a short demo GIF.
- Add deployment documentation after a real hosted environment exists.

## Screenshots

Place final screenshots in `docs/screenshots/`:

- `initial-state.png`
- `generated-workflow-canvas.png`
- `waiting-for-approval.png`
- `completed-reports.png`
- `logs-node-results.png`

## Demo GIF

Placeholder: `docs/screenshots/demo.gif`

The GIF should show workflow generation, run start, approval, and final artifacts. Do not add a GIF until it is captured from the working app.
