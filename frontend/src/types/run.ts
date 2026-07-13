import type { Approval, ApprovalPanelData } from "./approval";
import type { Artifact } from "./artifact";
import type {
  CompletionSummaryData,
  DemoMode,
  GuidedSteps,
  ModeExplanations,
  NextAction
} from "./ui";

export type RunStatus =
  | "pending"
  | "running"
  | "waiting_for_approval"
  | "completed"
  | "failed"
  | "cancelled"
  | "skipped"
  | string;

export type NodeStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "waiting_for_approval"
  | "skipped"
  | "cancelled"
  | string;

export type LogSeverity = "debug" | "info" | "warning" | "error" | string;

export interface RunNode {
  node_id: string;
  id?: string | null;
  type?: string | null;
  name?: string | null;
  subtitle?: string | null;
  status: NodeStatus;
  order?: number | null;
  stage?: number | null;
  dependencies?: string[];
  output?: Record<string, unknown> | null;
  error?: Record<string, unknown> | null;
  retry_count: number;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
  display?: {
    icon?: string;
    status_label?: string;
    summary?: string;
    severity?: string;
    is_risky?: boolean;
    is_approval_gate?: boolean;
  };
  output_summary?: NodeResultSummary | null;
}

export interface RunLog {
  timestamp?: string;
  node_id?: string;
  severity?: LogSeverity;
  message?: string;
  event?: string;
  details?: Record<string, unknown>;
}

export interface Run {
  run_id: string;
  workflow_id: string;
  status: RunStatus;
  summary?: RunSummary;
  started_at?: string | null;
  completed_at?: string | null;
  nodes: RunNode[];
  timeline?: RunTimelineEntry[];
  approval?: ApprovalPanelData | null;
  logs: RunLog[];
  node_outputs: Record<string, Record<string, unknown> | null>;
  node_results?: NodeResultSummary[];
  errors: Record<string, unknown>[];
  artifacts: Artifact[];
  artifact_tabs?: Record<string, ArtifactTabState>;
  pending_approval?: Approval | null;
  ui_state?: RunUiState;
  inspector?: Record<string, unknown>;
  layout?: {
    direction: string;
    nodes: Array<{ id: string; x: number; y: number }>;
  } | null;
  mode?: string | null;
  guided_steps?: GuidedSteps;
  next_action?: NextAction;
  mode_explanations?: ModeExplanations;
  demo_mode?: DemoMode;
  completion_summary?: CompletionSummaryData | null;
}

export interface RunListResponse {
  runs: Run[];
  limit: number;
  offset: number;
}

export interface RunSummary {
  title: string;
  repo_url?: string | null;
  mode?: string | null;
  nodes_total: number;
  nodes_completed: number;
  nodes_failed: number;
  nodes_skipped: number;
  nodes_waiting: number;
  artifacts_count: number;
  started_at?: string | null;
  completed_at?: string | null;
  active_node_id?: string | null;
  next_required_action?: string | null;
}

export interface RunTimelineEntry {
  node_id: string;
  name: string;
  status: NodeStatus;
  timestamp?: string | null;
  message: string;
  severity?: LogSeverity;
}

export interface NodeResultSummary {
  node_id: string;
  title: string;
  summary: string;
  metrics: Record<string, unknown>;
}

export interface ArtifactTabState {
  available: boolean;
  artifact_id?: string | null;
}

export interface RunUiState {
  primary_view: string;
  recommended_tab: string;
  canvas_focus_node_id?: string | null;
  show_approval_panel: boolean;
  show_reports_panel: boolean;
  show_completion_summary: boolean;
  banner?: {
    type: "success" | "warning" | "info" | "error" | string;
    title: string;
    message: string;
  } | null;
}
