export type GuidedStepStatus =
  | "pending"
  | "active"
  | "completed"
  | "failed"
  | "skipped"
  | string;

export interface GuidedStep {
  id: string;
  label: string;
  status: GuidedStepStatus;
  description: string;
}

export interface GuidedSteps {
  current_step: string;
  steps: GuidedStep[];
}

export interface NextAction {
  title: string;
  description: string;
  primary_label?: string | null;
  secondary_label?: string | null;
  target_tab?: string | null;
  target_node_id?: string | null;
  severity?: "info" | "warning" | "error" | string;
}

export interface ModeExplanation {
  mode: string;
  label: string;
  description: string;
}

export interface ModeExplanations {
  mcp: ModeExplanation;
  agent: ModeExplanation;
  storage: ModeExplanation;
}

export interface DemoMode {
  active: boolean;
  label: string;
  description: string;
}

export interface WorkflowReview {
  title: string;
  plain_english_summary: string;
  reads: string[];
  writes: Array<{
    label: string;
    requires_approval: boolean;
    mode: string;
  }>;
  approval_required: boolean;
  risk_level: string;
  estimated_outputs: string[];
}

export interface CompletionSummaryData {
  title: string;
  description: string;
  artifact_count: number;
  issue_creation: {
    mode: string;
    created_count: number;
    message: string;
  };
  primary_outputs: Array<{ type: string; label: string }>;
}
