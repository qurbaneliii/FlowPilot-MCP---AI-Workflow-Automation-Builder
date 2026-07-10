# Frontend UX

## Phase 7 UI Refinement

Phase 7 UI refinement is complete locally.

The FlowPilot frontend now uses a staged experience:

- Generate mode: focused prompt, GitHub repo URL input, example prompts, and concise product framing.
- Active workflow mode: compact workflow summary, dedicated workflow canvas, contextual run/approval panel, and lower workspace tabs.

The workflow canvas is now the main workspace after generation. It has stable sizing, a toolbar, deterministic node placement, custom nodes, readable edges, and selected-node inspection without squeezing the graph.

Approval, reports, logs, and node results are organized through contextual panels and tabs. Approval becomes prominent while the run is waiting for human review; reports become the primary lower tab after completion. Logs and raw node output stay available but secondary.

## Backend UI Alignment

The frontend now prefers backend-provided view data before falling back to local inference:

- Header status uses health `services` and `ui` labels, including non-blocking `Memory mode` for local/demo storage.
- The generated workflow summary bar uses backend `summary`; canvas nodes use backend `node_display` and optional layout hints.
- Run context panels use backend `summary`, `timeline`, `approval`, `ui_state`, and node `display.summary`.
- Workspace tabs follow `ui_state.recommended_tab` after run state changes and focus the canvas with `ui_state.canvas_focus_node_id`.
- Report tabs use backend `artifact_tabs` and artifact `display` hints, so an existing LinkedIn draft artifact cannot be paired with an empty-state message.
- Raw node outputs remain available in collapsible details for debugging.

Screenshots for README, LinkedIn, portfolio, and demo walkthroughs should be captured into `docs/screenshots/`.
