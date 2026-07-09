# Frontend UX

## Phase 7 UI Refinement

Phase 7 UI refinement is complete locally.

The FlowPilot frontend now uses a staged experience:

- Generate mode: focused prompt, GitHub repo URL input, example prompts, and concise product framing.
- Active workflow mode: compact workflow summary, dedicated workflow canvas, contextual run/approval panel, and lower workspace tabs.

The workflow canvas is now the main workspace after generation. It has stable sizing, a toolbar, deterministic node placement, custom nodes, readable edges, and selected-node inspection without squeezing the graph.

Approval, reports, logs, and node results are organized through contextual panels and tabs. Approval becomes prominent while the run is waiting for human review; reports become the primary lower tab after completion. Logs and raw node output stay available but secondary.

Screenshots for README, LinkedIn, portfolio, and demo walkthroughs should be captured into `docs/screenshots/`.
