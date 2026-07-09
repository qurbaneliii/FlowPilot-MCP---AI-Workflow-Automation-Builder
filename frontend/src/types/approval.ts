import type { IssueDraft } from "./artifact";

export type ApprovalStatus = "pending" | "approved" | "rejected" | string;
export type RiskLevel = "low" | "medium" | "high" | string;

export interface Approval {
  approval_id: string;
  status: ApprovalStatus;
  node_id: string;
  approval_summary?: string | null;
  issue_drafts: IssueDraft[];
  target_repository?: string | null;
  risk_level?: RiskLevel | null;
  downstream_action?: string | null;
  node_to_resume_after_approval?: string | null;
}

export interface ApprovalDecisionResponse {
  approval_id: string;
  decision: "approved" | "rejected" | string;
}
