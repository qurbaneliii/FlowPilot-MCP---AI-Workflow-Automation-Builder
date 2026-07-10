# Frontend UX

The FlowPilot frontend is a workflow operations surface. It should feel like a compact automation builder, not a chat window or marketing page.

## Product Flow

1. User enters an automation prompt and GitHub repository URL.
2. Frontend calls `POST /api/v1/workflows/generate`.
3. Backend returns a workflow graph plus summary, node display metadata, and layout hints.
4. User reviews the generated graph.
5. User starts the run.
6. Frontend polls `GET /api/v1/runs/{run_id}`.
7. If the run waits for approval, the approval panel becomes the primary action.
8. After completion, the reports tab becomes the recommended workspace.

## Main UI Regions

### Header

Uses backend health `services` and `ui` labels:

- `Backend connected`
- `Memory mode`
- `Mock MCP`
- `Fake agent mode`

The frontend should only display red service status when the backend marks a service as `blocking: true`.

### Start View

Includes:

- prompt textarea
- GitHub repository URL input
- example prompts
- structured error display
- loading state

### Workflow Summary Bar

Uses backend `workflow.summary`:

- workflow name
- repository URL
- node count
- risky action count
- approval requirement
- mode
- validation label

### Workflow Canvas

Uses React Flow custom nodes. Node display prefers backend metadata:

- `node_display.name`
- `node_display.subtitle`
- `node_display.icon`
- `node_display.stage`
- run `nodes[].display.summary`
- run `nodes[].display.severity`

The canvas can fall back to local mapping if older API fields are missing.

### Context Panel

Changes based on run state:

- no run: workflow overview
- running: run context, selected node inspector, timeline
- waiting for approval: approval card
- completed: completion summary and report link

The selected node defaults to `run.ui_state.canvas_focus_node_id`.

### Workspace Tabs

Tabs:

- Overview
- Approval
- Reports
- Logs
- Node Results

The default tab follows `run.ui_state.recommended_tab`.

### Reports

The reports panel uses backend `artifact_tabs` and artifact display metadata. If `linkedin_post_draft.available` is true, the frontend must not show a LinkedIn empty state.

### Logs and Node Results

The logs panel prefers backend `timeline` entries when raw logs are empty. The node results panel prefers backend `node_results` and `nodes[].output_summary`, while preserving raw JSON in collapsible details.

## Required States

The UI includes:

- loading states during workflow generation and run start
- error states for API failures
- empty states for no workflow, no reports, and no approval
- approval pending state
- completed reports state
- raw debug output details

## Visual Guidelines

- Keep the canvas as the primary workspace after generation.
- Keep reports, logs, and raw node outputs secondary but easy to inspect.
- Use compact status chips and stable dimensions.
- Do not show contradictory empty states when backend artifacts exist.
- Do not claim real external writes when the run is in mock mode.

## Verification

Expected frontend checks:

```powershell
cd frontend
npm run typecheck
npm run lint
npm run build
```

Manual smoke path:

1. Load frontend.
2. Confirm health labels are UI-friendly.
3. Generate workflow.
4. Confirm summary and canvas use backend display data.
5. Run workflow.
6. Confirm approval panel appears.
7. Approve.
8. Confirm reports appear and no generated artifact tab shows an empty state.

Final local visual acceptance on 2026-07-10 used a browser-driven mock-mode flow at 1440px, 1366px, and 1280px. It verified the start screen, generated workflow screen, dedicated canvas, all 9 nodes visible, no node overlap, no canvas clipping, no minimap, no red Next.js issue overlay, run start, waiting-for-approval state, primary approval panel, approve mock issue creation, completed state, reports/artifacts, LinkedIn draft without contradictory empty state, readable logs, and human-readable node results.
