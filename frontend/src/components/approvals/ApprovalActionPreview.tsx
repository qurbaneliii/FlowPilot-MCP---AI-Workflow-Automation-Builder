import { AlertTriangle, Github } from "lucide-react";
import type { Approval } from "@/types/approval";

interface ApprovalActionPreviewProps {
  approval: Approval;
  mode?: string | null;
}

export function ApprovalActionPreview({ approval, mode }: ApprovalActionPreviewProps) {
  return (
    <div className="rounded-md border border-status-approval/40 bg-status-approval/10 p-4">
      <div className="flex items-start gap-3">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-status-approval/45 bg-neutral-950">
          <Github className="h-5 w-5 text-status-approval" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="font-semibold text-neutral-50">GitHub issue creation</p>
          <p className="mt-1 text-sm leading-6 text-neutral-300">
            This action will create GitHub issues after approval. Mode is{" "}
            <span className="font-mono text-status-approval">{mode ?? "pending"}</span>.
          </p>
        </div>
      </div>
      <div className="mt-4 grid gap-2 text-sm sm:grid-cols-3">
        <PreviewMetric label="Repository" value={approval.target_repository ?? "Not provided"} />
        <PreviewMetric label="Issue drafts" value={String(approval.issue_drafts.length)} />
        <PreviewMetric label="Risk level" value={approval.risk_level ?? "medium"} />
      </div>
      <div className="mt-4 flex items-start gap-2 text-sm text-status-approval">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <p>{approval.approval_summary ?? "Approve creation of generated GitHub issue drafts."}</p>
      </div>
    </div>
  );
}

function PreviewMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-neutral-800 bg-neutral-950/70 p-3">
      <p className="font-mono text-[11px] uppercase tracking-normal text-neutral-500">
        {label}
      </p>
      <p className="mt-1 truncate text-sm font-medium text-neutral-100">{value}</p>
    </div>
  );
}
