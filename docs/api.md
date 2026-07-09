# FlowPilot MCP API

## GET `/api/v1/health`

Returns process health and lightweight dependency status.

Example response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "dependencies": {
    "database": "ok",
    "openai": "not_configured"
  }
}
```

The full workflow, run, and approval endpoints are scheduled for Phase 6 after the domain, persistence, MCP, agent, and node-handler layers exist.
