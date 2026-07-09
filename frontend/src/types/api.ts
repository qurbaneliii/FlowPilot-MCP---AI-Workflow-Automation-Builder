import type { ApprovalDecisionResponse } from "./approval";
import type { GeneratedWorkflow, Workflow } from "./workflow";
import type { Run, RunListResponse } from "./run";

export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface HealthResponse {
  status: "ok";
  version: string;
  dependencies: {
    database: "ok" | "error" | "not_configured";
    openai: "ok" | "error" | "not_configured";
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
