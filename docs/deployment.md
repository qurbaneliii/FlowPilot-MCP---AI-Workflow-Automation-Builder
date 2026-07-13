# Deployment

FlowPilot MCP is deployment-ready as an MVP. It is not an enterprise production system: API background execution remains in-process, authentication is not implemented, and a managed deployment still needs operational monitoring.

## Recommended Topology

- Frontend: Vercel, with `frontend/` as the project root.
- Backend: Render, Railway, Fly.io, or another container host.
- Database: Supabase PostgreSQL, Render PostgreSQL, Railway PostgreSQL, or equivalent.

The backend container runs `alembic upgrade head` and starts Uvicorn on `0.0.0.0:${PORT:-8000}`. The frontend must receive an API base URL ending in `/api/v1`.

## Backend Environment

```text
APP_ENV=production
APP_VERSION=0.1.0
STORAGE_MODE=postgres
DATABASE_URL=postgresql+asyncpg://...
DEFAULT_USER_ID=00000000-0000-0000-0000-000000000001
CORS_ORIGINS=https://your-frontend.vercel.app
OPENAI_AGENT_MODE=fake
OPENAI_AGENT_MODEL=gpt-4.1
OPENAI_API_KEY=
GITHUB_MCP_MODE=mock
GITHUB_MCP_SERVER_URL=
GITHUB_TOKEN=
FILESYSTEM_MCP_MODE=mock
FILESYSTEM_MCP_ROOT=/workspace
```

For a secrets-free demo, omit `DATABASE_URL` and set `STORAGE_MODE=memory`. Health will report `persistent: false` and `reset_on_restart: true`; do not present that mode as durable.

For real public GitHub reads, set `GITHUB_MCP_MODE=real`. `GITHUB_TOKEN` is optional for public reads but required for issue creation. Use a least-privilege fine-grained token limited to a safe repository. Real OpenAI agents require both `OPENAI_AGENT_MODE=real` and `OPENAI_API_KEY`.

## Vercel Frontend

1. Import the repository and set the root directory to `frontend`.
2. Set `NEXT_PUBLIC_API_BASE_URL=https://your-backend.example/api/v1`.
3. Deploy with the existing Next.js build command.
4. Add the final Vercel origin to backend `CORS_ORIGINS` and redeploy the backend.

## Render or Railway Backend

1. Create a Docker web service from the repository with `backend/` as the Docker context, or use `backend/Dockerfile` explicitly.
2. Attach managed PostgreSQL and provide its asyncpg-compatible `DATABASE_URL`.
3. Add the backend environment variables above.
4. Confirm the platform supplies `PORT`; the container command consumes it automatically.
5. Deploy and verify `GET https://your-backend.example/api/v1/health` reports `Postgres connected` and `persistent: true`.

For a non-container start command, use:

```text
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Deployment Smoke Test

1. Open the deployed frontend and confirm backend, GitHub, agent, and storage badges.
2. Generate the nine-node GitHub audit graph.
3. Run it to `waiting_for_approval`.
4. Confirm no issue exists before approval.
5. Approve in mock mode and confirm one explicit mock URL plus four artifacts.
6. Restart the backend in Postgres mode and fetch the same run again.
7. Only then test real GitHub writes against a safe repository, and verify an approval retry does not duplicate issues.

## Troubleshooting

- `CORS` error: add the exact frontend origin to the comma-separated `CORS_ORIGINS` value.
- Frontend 404/API errors: ensure `NEXT_PUBLIC_API_BASE_URL` includes `/api/v1`.
- `Postgres unavailable`: verify the async driver scheme, network allowlist, and migrations.
- GitHub 401/403: verify token validity, repository scope, issue permission, and rate-limit headers.
- Memory mode after deployment: `DATABASE_URL` is missing or `STORAGE_MODE=memory` was explicitly set.

No hosted deployment was executed during the 2026-07-13 final pass because Vercel/Render/Railway/Fly credentials and CLIs were unavailable in the environment.
