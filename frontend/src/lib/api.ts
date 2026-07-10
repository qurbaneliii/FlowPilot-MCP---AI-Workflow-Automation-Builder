import { API_BASE_URL } from "./constants";
import type {
  ApiError,
  ApprovalDecisionWithRun,
  GenerateWorkflowRequest,
  GeneratedWorkflow,
  HealthResponse,
  Run,
  RunListResponse,
  RunWorkflowResponse,
  Workflow
} from "@/types/api";

export class FlowPilotApiError extends Error implements ApiError {
  status: number;
  code: string;
  details?: Record<string, unknown>;
  severity?: string;
  retryable?: boolean;

  constructor(error: ApiError) {
    super(error.message);
    this.name = "FlowPilotApiError";
    this.status = error.status;
    this.code = error.code;
    this.details = error.details;
    this.severity = error.severity;
    this.retryable = error.retryable;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    throw new FlowPilotApiError(normalizeApiError(response.status, payload));
  }
  return payload as T;
}

function normalizeApiError(status: number, payload: unknown): ApiError {
  if (
    payload &&
    typeof payload === "object" &&
    "error" in payload &&
    typeof payload.error === "object" &&
    payload.error !== null
  ) {
    const error = payload.error as Record<string, unknown>;
    return {
      status,
      code: typeof error.code === "string" ? error.code : "API_ERROR",
      message:
        typeof error.message === "string"
          ? error.message
          : "The FlowPilot API returned an error.",
      details:
        error.details && typeof error.details === "object"
          ? (error.details as Record<string, unknown>)
          : undefined,
      severity: typeof error.severity === "string" ? error.severity : undefined,
      retryable: typeof error.retryable === "boolean" ? error.retryable : undefined
    };
  }
  return {
    status,
    code: "API_ERROR",
    message: "The FlowPilot API returned an unexpected response."
  };
}

export function generateWorkflow(
  body: GenerateWorkflowRequest
): Promise<GeneratedWorkflow> {
  return request<GeneratedWorkflow>("/workflows/generate", {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export function getWorkflow(workflowId: string): Promise<Workflow> {
  return request<Workflow>(`/workflows/${workflowId}`);
}

export function runWorkflow(workflowId: string): Promise<RunWorkflowResponse> {
  return request<RunWorkflowResponse>("/workflows/run", {
    method: "POST",
    body: JSON.stringify({ workflow_id: workflowId })
  });
}

export function getRun(runId: string): Promise<Run> {
  return request<Run>(`/runs/${runId}`);
}

export function listRuns(limit = 20, offset = 0): Promise<RunListResponse> {
  return request<RunListResponse>(`/runs?limit=${limit}&offset=${offset}`);
}

export function approveApproval(
  approvalId: string,
  reason?: string
): Promise<ApprovalDecisionWithRun> {
  return request<ApprovalDecisionWithRun>(`/approvals/${approvalId}/approve`, {
    method: "POST",
    body: JSON.stringify({ reason: reason ?? null })
  });
}

export function rejectApproval(
  approvalId: string,
  reason?: string
): Promise<ApprovalDecisionWithRun> {
  return request<ApprovalDecisionWithRun>(`/approvals/${approvalId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason: reason ?? null })
  });
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}
