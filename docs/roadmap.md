# Roadmap

This roadmap is intentionally honest about the current MVP. FlowPilot is a serious portfolio project, with production hardening still ahead.

## Complete Locally

- Pure workflow graph validation and execution engine
- Node registry and production node handlers
- Agent abstraction layer with fake/unavailable/real modes
- MCP-style client ports and registry
- GitHub Repository Audit MVP graph
- Human approval before GitHub issue creation
- Markdown artifact generation
- FastAPI MVP endpoints
- UI-friendly backend response view models
- Next.js workflow dashboard
- Backend and frontend test/check commands
- Docker Compose stack definition and verification scripts

## Near-Term Improvements

- Wire API runtime to durable PostgreSQL repositories instead of in-process store state.
- Add persistent background worker execution rather than in-process background tasks.
- Capture final screenshots and `docs/screenshots/demo.gif`.
- Add a small seeded demo mode that can run without external credentials.
- Add more workflow examples and fixture snapshots.
- Add browser-based E2E tests for the full frontend flow.

## Integration Improvements

- Document real GitHub MCP setup with token scopes.
- Document real OpenAI agent mode setup.
- Add environment validation for real mode misconfiguration.
- Add safer filesystem real-mode examples with scoped roots.

## Product Improvements

- More workflow templates beyond GitHub repo audit.
- Branching workflows using the `condition` node.
- Richer artifact previews and export options.
- Run history search and filtering.
- Better retry/resume controls for failed runs.

## Production Hardening

- Authentication and user/project scoping.
- Durable queues and worker isolation.
- Database-backed run state for API runtime.
- Secrets management.
- Audit log persistence.
- Rate limiting.
- Deployment documentation after a real hosted environment exists.

## Explicit Non-Goals for Current MVP

- Broad no-code automation-suite replacement
- Production deployment without the hardening work listed above
- Guaranteed real OpenAI/MCP execution without configuration
- Autonomous external writes without human approval
