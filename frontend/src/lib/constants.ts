import {
  AlertTriangle,
  CheckCircle2,
  Circle,
  Clock3,
  FileText,
  GitBranch,
  Github,
  Loader2,
  PauseCircle,
  PenLine,
  ShieldAlert,
  SkipForward,
  Sparkles,
  Terminal,
  XCircle
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { NodeStatus, RunStatus } from "@/types/run";
import type { WorkflowNodeType } from "@/types/workflow";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export const TERMINAL_RUN_STATUSES = new Set<RunStatus>([
  "completed",
  "failed",
  "cancelled"
]);

export const ACTIVE_RUN_STATUSES = new Set<RunStatus>([
  "pending",
  "running",
  "waiting_for_approval"
]);

export const STATUS_META: Record<
  string,
  {
    label: string;
    className: string;
    dotClassName: string;
    icon: LucideIcon;
  }
> = {
  pending: {
    label: "Pending",
    className: "border-status-skipped/40 bg-status-skipped/10 text-neutral-300",
    dotClassName: "bg-status-skipped",
    icon: Clock3
  },
  running: {
    label: "Running",
    className: "border-status-running/50 bg-status-running/10 text-status-running",
    dotClassName: "bg-status-running",
    icon: Loader2
  },
  completed: {
    label: "Completed",
    className: "border-status-success/50 bg-status-success/10 text-status-success",
    dotClassName: "bg-status-success",
    icon: CheckCircle2
  },
  failed: {
    label: "Failed",
    className: "border-status-danger/50 bg-status-danger/10 text-status-danger",
    dotClassName: "bg-status-danger",
    icon: XCircle
  },
  waiting_for_approval: {
    label: "Waiting for approval",
    className:
      "border-status-approval/60 bg-status-approval/10 text-status-approval",
    dotClassName: "bg-status-approval",
    icon: PauseCircle
  },
  skipped: {
    label: "Skipped",
    className: "border-status-skipped/40 bg-status-skipped/10 text-status-skipped",
    dotClassName: "bg-status-skipped",
    icon: SkipForward
  },
  cancelled: {
    label: "Cancelled",
    className: "border-status-skipped/40 bg-status-skipped/10 text-status-skipped",
    dotClassName: "bg-status-skipped",
    icon: SkipForward
  }
};

export const NODE_TYPE_META: Record<
  string,
  { label: string; icon: LucideIcon; accent: string }
> = {
  manual_trigger: { label: "Trigger", icon: Sparkles, accent: "text-accent-300" },
  github_repo_reader: { label: "GitHub MCP", icon: Github, accent: "text-sky-300" },
  ai_repo_analyzer: {
    label: "AI analysis",
    icon: ShieldAlert,
    accent: "text-violet-300"
  },
  readme_reviewer: {
    label: "README review",
    icon: FileText,
    accent: "text-emerald-300"
  },
  issue_draft_generator: {
    label: "Issue drafts",
    icon: PenLine,
    accent: "text-amber-300"
  },
  human_approval: {
    label: "Approval gate",
    icon: AlertTriangle,
    accent: "text-amber-300"
  },
  github_issue_creator: {
    label: "Issue creation",
    icon: Github,
    accent: "text-red-300"
  },
  linkedin_draft_generator: {
    label: "LinkedIn draft",
    icon: PenLine,
    accent: "text-blue-300"
  },
  markdown_report_writer: {
    label: "Reports",
    icon: Terminal,
    accent: "text-emerald-300"
  },
  condition: { label: "Condition", icon: GitBranch, accent: "text-neutral-300" }
};

export const EXAMPLE_PROMPTS = [
  "Audit this GitHub repository and draft guarded improvement issues.",
  "Review README quality, CI readiness, and deployment risks before creating issues.",
  "Generate a portfolio-readiness audit with LinkedIn demo copy."
];

export function getStatusMeta(status?: NodeStatus | RunStatus | null) {
  return STATUS_META[status ?? "pending"] ?? STATUS_META.pending;
}

export function getNodeTypeMeta(type: WorkflowNodeType) {
  return (
    NODE_TYPE_META[type] ?? {
      label: type.replaceAll("_", " "),
      icon: Circle,
      accent: "text-neutral-300"
    }
  );
}
