import type { Approval } from "./approval";
import type { Artifact } from "./artifact";

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
  status: NodeStatus;
  output?: Record<string, unknown> | null;
  error?: Record<string, unknown> | null;
  retry_count: number;
  started_at?: string | null;
  completed_at?: string | null;
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
  started_at?: string | null;
  completed_at?: string | null;
  nodes: RunNode[];
  logs: RunLog[];
  node_outputs: Record<string, Record<string, unknown> | null>;
  errors: Record<string, unknown>[];
  artifacts: Artifact[];
  pending_approval?: Approval | null;
  mode?: string | null;
}

export interface RunListResponse {
  runs: Run[];
  limit: number;
  offset: number;
}
