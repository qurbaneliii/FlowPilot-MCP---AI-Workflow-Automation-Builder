import { EmptyState } from "@/components/layout/EmptyState";
import { StatusPill } from "@/components/layout/StatusPill";
import { getNodeTypeMeta } from "@/lib/constants";
import { formatTimestamp, summarizeUnknown } from "@/lib/formatters";
import type { Run } from "@/types/run";
import type { WorkflowGraph } from "@/types/workflow";
import { Search } from "lucide-react";

interface NodeInspectorProps {
  graph?: WorkflowGraph | null;
  run?: Run | null;
  selectedNodeId?: string | null;
}

export function NodeInspector({ graph, run, selectedNodeId }: NodeInspectorProps) {
  const node =
    graph?.nodes.find((candidate) => candidate.id === selectedNodeId) ??
    graph?.nodes.find((candidate) => candidate.type === "human_approval") ??
    graph?.nodes[0];
  if (!node) {
    return (
      <EmptyState
        icon={Search}
        title="No node selected"
        description="Generate a graph and select a node to inspect configuration, status, and output."
      />
    );
  }
  const runNode = run?.nodes.find((candidate) => candidate.node_id === node.id);
  const meta = getNodeTypeMeta(node.type);
  const Icon = meta.icon;
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <Icon className={`h-5 w-5 shrink-0 ${meta.accent}`} aria-hidden="true" />
          <div className="min-w-0">
            <h3 className="truncate text-sm font-semibold text-neutral-50">{node.name}</h3>
            <p className="font-mono text-[11px] uppercase tracking-normal text-neutral-500">
              {meta.label}
            </p>
          </div>
        </div>
        <StatusPill status={runNode?.status ?? "pending"} compact />
      </div>
      <dl className="grid gap-2 text-sm">
        <Info label="Started" value={formatTimestamp(runNode?.started_at)} />
        <Info label="Completed" value={formatTimestamp(runNode?.completed_at)} />
        <Info label="Retries" value={String(runNode?.retry_count ?? 0)} />
        <Info label="Dependencies" value={node.dependencies.join(", ") || "None"} />
      </dl>
      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-normal text-neutral-500">
          Output summary
        </p>
        <div className="rounded-md border border-neutral-800 bg-neutral-950/70 p-3 text-sm leading-6 text-neutral-300">
          {runNode?.error
            ? String(runNode.error.message ?? "Node failed.")
            : summarizeUnknown(runNode?.output)}
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3 rounded-md border border-neutral-800 bg-neutral-950/50 px-3 py-2">
      <dt className="text-neutral-500">{label}</dt>
      <dd className="truncate text-right text-neutral-200">{value}</dd>
    </div>
  );
}
