import { CheckCircle2, ShieldAlert } from "lucide-react";
import { StatusPill } from "@/components/layout/StatusPill";
import { getNodeTypeMeta } from "@/lib/constants";
import { getWorkflowSummary } from "@/lib/workflowMapper";
import type { GeneratedWorkflow } from "@/types/workflow";

interface GeneratedWorkflowPreviewProps {
  workflow?: GeneratedWorkflow | null;
}

export function GeneratedWorkflowPreview({ workflow }: GeneratedWorkflowPreviewProps) {
  const summary = getWorkflowSummary(workflow?.workflow);
  if (!workflow) {
    return (
      <div className="rounded-md border border-neutral-800 bg-neutral-950/60 p-4 text-sm text-neutral-400">
        Generated workflow metadata will appear here before execution.
      </div>
    );
  }
  return (
    <div className="space-y-4">
      <div className="rounded-md border border-neutral-800 bg-neutral-950/60 p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-neutral-50">{summary.name}</h3>
            <p className="mt-1 text-sm leading-6 text-neutral-400">
              {summary.description}
            </p>
          </div>
          <StatusPill status="completed" label="Validated" />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
          <Metric label="Nodes" value={summary.nodeCount} />
          <Metric label="Risky actions" value={summary.riskyActionCount} />
          <Metric label="Stages" value={summary.estimatedStages} />
          <Metric label="Approval" value={summary.approvalRequired ? "Required" : "None"} />
        </div>
      </div>
      <div className="space-y-2">
        {workflow.workflow.nodes.map((node) => {
          const meta = getNodeTypeMeta(node.type);
          const Icon = meta.icon;
          return (
            <div
              key={node.id}
              className="flex items-center justify-between gap-3 rounded-md border border-neutral-800 bg-neutral-950/50 px-3 py-2"
            >
              <div className="flex min-w-0 items-center gap-2">
                <Icon className={`h-4 w-4 shrink-0 ${meta.accent}`} aria-hidden="true" />
                <div className="min-w-0">
                  <p className="truncate text-sm text-neutral-100">{node.name}</p>
                  <p className="font-mono text-[11px] text-neutral-500">{meta.label}</p>
                </div>
              </div>
              {node.type === "human_approval" ? (
                <ShieldAlert className="h-4 w-4 shrink-0 text-status-approval" />
              ) : (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-status-success" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md border border-neutral-800 bg-neutral-900/70 p-2">
      <p className="font-mono text-[11px] uppercase tracking-normal text-neutral-500">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold text-neutral-100">{value}</p>
    </div>
  );
}
