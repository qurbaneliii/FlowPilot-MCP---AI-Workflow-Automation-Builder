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

export interface ApprovalPanelData {
  approval_id: string;
  status: ApprovalStatus;
  title: string;
  description: string;
  target_action?: string | null;
  target_repository?: string | null;
  mode?: string | null;
  risk_level?: RiskLevel | null;
  issue_count: number;
  issue_previews: Array<{
    title: string;
    priority?: string | null;
    labels: string[];
    body_preview: string;
  }>;
  issue_drafts: IssueDraft[];
  can_approve: boolean;
  can_reject: boolean;
}

export interface ApprovalDecisionResponse {
  approval_id: string;
  status: "approved" | "rejected" | string;
  decision: "approved" | "rejected" | string;
  run_id: string;
  message: string;
  run_status: string;
  next_poll_recommended: boolean;
}
