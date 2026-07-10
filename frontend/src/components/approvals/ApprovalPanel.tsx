"use client";

import { Check, X } from "lucide-react";
import { ErrorState } from "@/components/layout/ErrorState";
import { EmptyState } from "@/components/layout/EmptyState";
import { ApprovalActionPreview } from "./ApprovalActionPreview";
import type { Approval, ApprovalPanelData } from "@/types/approval";
import { ShieldCheck } from "lucide-react";

interface ApprovalPanelProps {
  approval?: Approval | ApprovalPanelData | null;
  mode?: string | null;
  loadingDecision?: "approve" | "reject" | null;
  error?: string | null;
  lastDecision?: string | null;
  onApprove: (approvalId: string) => void;
  onReject: (approvalId: string) => void;
}

export function ApprovalPanel({
  approval,
  mode,
  loadingDecision,
  error,
  lastDecision,
  onApprove,
  onReject
}: ApprovalPanelProps) {
  if (!approval) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title={lastDecision ? `Approval ${lastDecision}` : "No approval waiting"}
        description="The workflow will pause here when a human must approve a guarded action."
      />
    );
  }
  const isLoading = Boolean(loadingDecision);
  const issueDrafts = "issue_drafts" in approval ? approval.issue_drafts : [];
  const title =
    "title" in approval ? approval.title : "Human approval required";
  const description =
    "description" in approval
      ? approval.description
      : "FlowPilot paused because this step can create external GitHub issues.";
  return (
    <div className="space-y-4">
      <div>
        <p className="font-mono text-[11px] uppercase tracking-normal text-status-approval">
          Human approval required
        </p>
        <h3 className="mt-1 text-lg font-semibold text-neutral-50">
          {title}
        </h3>
        <p className="mt-2 text-sm leading-6 text-neutral-300">
          {description}
        </p>
      </div>
      <ApprovalActionPreview approval={approval} mode={mode} />
      <div className="space-y-2">
        {issueDrafts.slice(0, 3).map((issue) => (
          <div key={issue.title} className="rounded-md border border-neutral-800 bg-neutral-950/55 p-3">
            <p className="text-sm font-medium text-neutral-100">{issue.title}</p>
            <p className="mt-1 line-clamp-2 text-sm leading-6 text-neutral-400">
              {issue.body}
            </p>
          </div>
        ))}
      </div>
      {error && <ErrorState title="Approval action failed" message={error} />}
      <div className="grid gap-2 sm:grid-cols-2">
        <button
          type="button"
          className="btn-primary"
          disabled={isLoading}
          onClick={() => onApprove(approval.approval_id)}
        >
          <Check className="h-4 w-4" aria-hidden="true" />
          {loadingDecision === "approve" ? "Approving..." : "Approve"}
        </button>
        <button
          type="button"
          className="btn-danger"
          disabled={isLoading}
          onClick={() => onReject(approval.approval_id)}
        >
          <X className="h-4 w-4" aria-hidden="true" />
          {loadingDecision === "reject" ? "Rejecting..." : "Reject"}
        </button>
      </div>
    </div>
  );
}
