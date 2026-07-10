"use client";

import { useState } from "react";
import { ApprovalPanel } from "@/components/approvals/ApprovalPanel";
import { EmptyState } from "@/components/layout/EmptyState";
import { NodeResultViewer } from "@/components/runs/NodeResultViewer";
import { RunLogsPanel } from "@/components/runs/RunLogsPanel";
import { RunSummaryPanel } from "@/components/runs/RunSummaryPanel";
import { RunTimeline } from "@/components/runs/RunTimeline";
import { OutputReportsPanel } from "@/components/reports/OutputReportsPanel";
import type { Run } from "@/types/run";
import type { WorkflowGraph } from "@/types/workflow";
import { FileText, ShieldCheck } from "lucide-react";

type TabId = "overview" | "approval" | "reports" | "logs" | "node-results";

interface WorkspaceTabsProps {
  graph?: WorkflowGraph | null;
  run?: Run | null;
  mode?: string | null;
  loadingDecision?: "approve" | "reject" | null;
  approvalError?: string | null;
  lastDecision?: string | null;
  onSelectNode: (nodeId: string) => void;
  onApprove: (approvalId: string) => void;
  onReject: (approvalId: string) => void;
}

const tabs: Array<{ id: TabId; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "approval", label: "Approval" },
  { id: "reports", label: "Reports" },
  { id: "logs", label: "Logs" },
  { id: "node-results", label: "Node Results" }
];

export function WorkspaceTabs({
  graph,
  run,
  mode,
  loadingDecision,
  approvalError,
  lastDecision,
  onSelectNode,
  onApprove,
  onReject
}: WorkspaceTabsProps) {
  const [manualTab, setManualTab] = useState<{
    tab: TabId;
    stateKey: string;
  } | null>(null);
  const backendRecommendedTab = normalizeTab(run?.ui_state?.recommended_tab);
  const stateKey = `${run?.status ?? "idle"}:${run?.ui_state?.recommended_tab ?? "overview"}`;
  const recommendedTab: TabId =
    backendRecommendedTab ??
    (run?.status === "waiting_for_approval"
      ? "approval"
      : run?.status === "completed"
        ? "reports"
        : "overview");
  const activeTab =
    manualTab?.stateKey === stateKey ? manualTab.tab : recommendedTab;

  return (
    <section className="section-card" id="reports">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="kicker">Lower workspace</p>
          <h2 className="mt-1 text-lg font-semibold text-neutral-50">
            Review outputs without crowding the canvas
          </h2>
        </div>
        <div className="flex gap-2 overflow-x-auto rounded-md border border-neutral-800 bg-neutral-950/55 p-1">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            const needsAttention =
              tab.id === "approval" && run?.status === "waiting_for_approval";
            return (
              <button
                key={tab.id}
                type="button"
                className={`workspace-tab ${isActive ? "workspace-tab-active" : ""} ${
                  needsAttention ? "workspace-tab-attention" : ""
                }`}
                onClick={() => setManualTab({ tab: tab.id, stateKey })}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {activeTab === "overview" && (
        <div className="grid gap-5 lg:grid-cols-[360px_1fr]">
          <RunSummaryPanel run={run} />
          <RunTimeline graph={graph} run={run} onSelectNode={onSelectNode} />
        </div>
      )}
      {activeTab === "approval" && (run?.approval ?? run?.pending_approval) && (
        <EmptyState
          icon={ShieldCheck}
          title="Approval is active in the context panel"
          description="FlowPilot paused before creating GitHub issues. Review and resolve the approval card next to the workflow canvas."
        />
      )}
      {activeTab === "approval" && run && !(run.approval ?? run.pending_approval) && (
        <ApprovalPanel
          approval={run?.approval ?? run?.pending_approval}
          mode={mode}
          loadingDecision={loadingDecision}
          error={approvalError}
          lastDecision={lastDecision}
          onApprove={onApprove}
          onReject={onReject}
        />
      )}
      {activeTab === "reports" && run && <OutputReportsPanel run={run} />}
      {activeTab === "logs" && <RunLogsPanel run={run} />}
      {activeTab === "node-results" && <NodeResultViewer run={run} />}
      {!run && activeTab === "reports" && (
        <EmptyState
          icon={FileText}
          title="No reports generated yet"
          description="Run and approve the workflow to render audit reports and draft artifacts."
        />
      )}
      {!run && activeTab === "approval" && (
        <EmptyState
          icon={ShieldCheck}
          title="No approval waiting"
          description="The approval tab will become active when FlowPilot pauses before GitHub issue creation."
        />
      )}
    </section>
  );
}

function normalizeTab(value?: string | null): TabId | null {
  if (
    value === "overview" ||
    value === "approval" ||
    value === "reports" ||
    value === "logs" ||
    value === "node-results"
  ) {
    return value;
  }
  return null;
}
