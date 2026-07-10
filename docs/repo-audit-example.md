# Repository Audit Example

The backend MVP now supports the full mocked GitHub repository audit flow:

1. Generate a workflow with `POST /api/v1/workflows/generate`.
2. Start a run with `POST /api/v1/workflows/run`.
3. Inspect `GET /api/v1/runs/{run_id}` until it reports `waiting_for_approval`.
4. Approve or reject the pending approval.
5. Inspect artifacts in the final run response.

In default local configuration, GitHub MCP runs in mock mode and OpenAI agents run in fake mode. Mock issue creation is explicit in node output with `mode: "mock"` and `display_url` values prefixed with `mock:`.
