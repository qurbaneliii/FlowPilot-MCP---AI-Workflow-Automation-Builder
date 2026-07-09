"use client";

import { FileText, ShieldAlert } from "lucide-react";
import { ApprovalPanel } from "@/components/approvals/ApprovalPanel";
import { SectionCard } from "@/components/layout/SectionCard";
import { RunSummaryPanel } from "@/components/runs/RunSummaryPanel";
import { RunTimeline } from "@/components/runs/RunTimeline";
import { NodeInspector } from "./NodeInspector";
import type { Approval } from "@/types/approval";
import type { Run } from "@/types/run";
import type { WorkflowGraph } from "@/types/workflow";

interface ContextPanelProps {
  graph?: WorkflowGraph | null;
  run?: Run | null;
  mode?: string | null;
  selectedNodeId?: string | null;
  loadingDecision?: "approve" | "reject" | null;
  approvalError?: string | null;
  lastDecision?: string | null;
  onSelectNode: (nodeId: string) => void;
  onApprove: (approvalId: string) => void;
  onReject: (approvalId: string) => void;
}

export function ContextPanel({
  graph,
  run,
  mode,
  selectedNodeId,
  loadingDecision,
  approvalError,
  lastDecision,
  onSelectNode,
  onApprove,
  onReject
}: ContextPanelProps) {
  const approval = run?.pending_approval;
  if (approval) {
    return (
      <SectionCard title="Approval Required" eyebrow="Primary action" className="approval-glow">
        <ApprovalPanel
          approval={approval as Approval}
          mode={mode}
          loadingDecision={loadingDecision}
          error={approvalError}
          lastDecision={lastDecision}
          onApprove={onApprove}
          onReject={onReject}
        />
      </SectionCard>
    );
  }

  if (run?.status === "completed") {
    return (
      <div className="space-y-4">
        <SectionCard
          title="Completion Summary"
          eyebrow="Reports ready"
          action={<FileText className="h-4 w-4 text-accent-300" aria-hidden="true" />}
        >
          <RunSummaryPanel run={run} />
          <a href="#reports" className="btn-primary mt-4 w-full">
            View generated reports
          </a>
        </SectionCard>
        <SectionCard title="Selected Node" eyebrow="Inspector">
          <NodeInspector graph={graph} run={run} selectedNodeId={selectedNodeId} />
        </SectionCard>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <SectionCard
        title={run ? "Run Context" : "Workflow Overview"}
        eyebrow={run ? "Execution" : "Generated graph"}
        action={<ShieldAlert className="h-4 w-4 text-accent-300" aria-hidden="true" />}
      >
        <RunSummaryPanel run={run} />
      </SectionCard>
      <SectionCard title="Selected Node" eyebrow="Inspector">
        <NodeInspector graph={graph} run={run} selectedNodeId={selectedNodeId} />
      </SectionCard>
      <SectionCard title="Timeline" eyebrow="Compact">
        <RunTimeline graph={graph} run={run} onSelectNode={onSelectNode} />
      </SectionCard>
    </div>
  );
}
