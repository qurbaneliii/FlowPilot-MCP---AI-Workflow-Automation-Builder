export type ArtifactType =
  | "repo_audit_report"
  | "readme_improvement_plan"
  | "github_issue_drafts"
  | "linkedin_post_draft"
  | string;

export type FindingSeverity = "info" | "warning" | "critical";

export type FindingCategory =
  | "documentation"
  | "setup"
  | "environment"
  | "testing"
  | "ci_cd"
  | "project_structure"
  | "security"
  | "deployment"
  | "portfolio_readiness"
  | "maintainability"
  | string;

export interface Artifact {
  artifact_id: string;
  run_id: string;
  artifact_type: ArtifactType;
  type?: ArtifactType;
  filename: string;
  title?: string | null;
  content: string;
  created_at: string;
  mode?: string | null;
  source_node_id?: string | null;
  display?: {
    tab?: string;
    empty?: boolean;
    copyable?: boolean;
    badge?: string;
  };
}

export interface AuditFinding {
  category: FindingCategory;
  severity: FindingSeverity;
  title: string;
  description: string;
  recommendation: string;
  affected_files: string[];
  suggested_issue_title?: string | null;
}

export interface RiskFlag {
  code: string;
  severity: FindingSeverity;
  description: string;
}

export interface GitHubAudit {
  summary: string;
  findings: AuditFinding[];
  risk_flags: RiskFlag[];
}

export interface IssueDraft {
  title: string;
  body: string;
  labels: string[];
  priority: "low" | "medium" | "high" | string;
  acceptance_criteria: string[];
  created?: boolean;
  url?: string;
  display_url?: string;
}

export interface LinkedInDraft {
  post_text: string;
  hashtags: string[];
  tone: "professional" | "technical" | "concise" | string;
}
