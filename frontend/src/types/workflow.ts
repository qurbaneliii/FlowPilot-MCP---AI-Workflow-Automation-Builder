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
}

export interface GeneratedWorkflow extends Workflow {
  validation: {
    valid: boolean;
    issues: string[];
    corrected_graph?: WorkflowGraph | null;
  };
  warnings: string[];
}

export interface WorkflowSummary {
  name: string;
  description: string;
  nodeCount: number;
  riskyActionCount: number;
  approvalRequired: boolean;
  estimatedStages: number;
}
