import type { ApprovalDecisionResponse } from "./approval";
import type { GeneratedWorkflow, Workflow } from "./workflow";
import type { Run, RunListResponse } from "./run";

export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, unknown>;
  severity?: "info" | "warning" | "error" | string;
  retryable?: boolean;
}

export interface HealthResponse {
  status: "ok";
  version: string;
  dependencies: {
    database: "ok" | "error" | "not_configured";
    openai: "ok" | "error" | "not_configured";
  };
  services?: Record<
    "backend" | "database" | "mcp" | "openai" | string,
    {
      status: string;
      label: string;
      severity: "success" | "warning" | "info" | "error" | string;
      blocking?: boolean;
    }
  >;
  ui?: {
    primary_mode_label: string;
    storage_mode_label: string;
    show_database_warning: boolean;
    database_warning_blocks_demo: boolean;
  };
}

export interface GenerateWorkflowRequest {
  prompt: string;
  repo_url: string;
}

export interface RunWorkflowResponse {
  run_id: string;
  status: string;
}

export interface ApprovalDecisionWithRun extends ApprovalDecisionResponse {
  run: Run;
}

export type { GeneratedWorkflow, Workflow, Run, RunListResponse };
