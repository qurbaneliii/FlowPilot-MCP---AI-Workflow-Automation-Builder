export type WorkflowNodeType =
  | "manual_trigger"
  | "github_repo_reader"
  | "ai_repo_analyzer"
  | "readme_reviewer"
  | "issue_draft_generator"
  | "human_approval"
  | "github_issue_creator"
  | "linkedin_draft_generator"
  | "markdown_report_writer"
  | "condition"
  | string;

export type WorkflowStatus = "idle" | "generated" | "invalid" | "ready";

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  name: string;
  config: Record<string, unknown>;
  dependencies: string[];
}

export interface WorkflowGraph {
  nodes: WorkflowNode[];
}

export interface Workflow {
  workflow_id: string;
  workflow: WorkflowGraph;
  metadata?: Record<string, unknown>;
  summary?: BackendWorkflowSummary | null;
  node_display?: BackendNodeDisplay[];
  layout?: BackendWorkflowLayout | null;
}

export interface GeneratedWorkflow extends Workflow {
  validation: {
    valid: boolean;
    issues: string[];
    corrected_graph?: WorkflowGraph | null;
  };
  summary?: BackendWorkflowSummary;
  node_display?: BackendNodeDisplay[];
  layout?: BackendWorkflowLayout | null;
  warnings: string[];
}

export interface WorkflowSummary {
  name: string;
  description: string;
  nodeCount: number;
  riskyActionCount: number;
  approvalRequired: boolean;
  estimatedStages: number;
  repoUrl?: string | null;
  mode?: string | null;
  statusLabel?: string;
}

export interface BackendWorkflowSummary {
  name: string;
  description: string;
  repo_url?: string | null;
  node_count: number;
  estimated_stages: number;
  risky_action_count: number;
  approval_required: boolean;
  mode?: string | null;
  status_label: string;
}

export interface BackendNodeDisplay {
  id: string;
  type: string;
  name: string;
  subtitle: string;
  icon: string;
  order: number;
  stage: number;
  dependencies: string[];
  risk_level: string;
  approval_required: boolean;
  description: string;
}

export interface BackendWorkflowLayout {
  direction: string;
  nodes: Array<{ id: string; x: number; y: number }>;
}
