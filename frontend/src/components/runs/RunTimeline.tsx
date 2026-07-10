import { StatusPill } from "@/components/layout/StatusPill";
import { getNodeOrder, nodeDisplayName } from "@/lib/workflowMapper";
import { formatTimestamp } from "@/lib/formatters";
import type { Run } from "@/types/run";
import type { WorkflowGraph } from "@/types/workflow";

interface RunTimelineProps {
  graph?: WorkflowGraph | null;
  run?: Run | null;
  onSelectNode?: (nodeId: string) => void;
}

export function RunTimeline({ graph, run, onSelectNode }: RunTimelineProps) {
  if (run?.timeline?.length) {
    return (
      <ol className="space-y-3">
        {run.timeline.map((entry, index) => (
          <li key={`${entry.node_id}-${index}`} className="relative pl-7">
            {index < (run.timeline?.length ?? 0) - 1 && (
              <span className="absolute left-[7px] top-5 h-[calc(100%+0.5rem)] w-px bg-neutral-800" />
            )}
            <span className="absolute left-0 top-1.5 h-3.5 w-3.5 rounded-full border border-neutral-700 bg-neutral-950" />
            <button
              type="button"
              onClick={() => onSelectNode?.(entry.node_id)}
              className="w-full rounded-md border border-neutral-800 bg-neutral-950/55 p-3 text-left transition hover:border-neutral-700 hover:bg-neutral-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent-300"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="truncate text-sm font-medium text-neutral-100">
                  {entry.name}
                </p>
                <StatusPill status={entry.status} compact />
              </div>
              <p className="mt-2 text-xs text-neutral-400">{entry.message}</p>
              <p className="mt-2 font-mono text-[11px] text-neutral-500">
                {formatTimestamp(entry.timestamp)}
              </p>
            </button>
          </li>
        ))}
      </ol>
    );
  }
  const order = getNodeOrder(graph);
  const runNodes = new Map((run?.nodes ?? []).map((node) => [node.node_id, node]));
  if (!order.length) {
    return (
      <p className="text-sm leading-6 text-neutral-400">
        Generate a workflow to see ordered node execution.
      </p>
    );
  }
  return (
    <ol className="space-y-3">
      {order.map((nodeId, index) => {
        const runNode = runNodes.get(nodeId);
        const status = runNode?.status ?? "pending";
        return (
          <li key={nodeId} className="relative pl-7">
            {index < order.length - 1 && (
              <span className="absolute left-[7px] top-5 h-[calc(100%+0.5rem)] w-px bg-neutral-800" />
            )}
            <span className="absolute left-0 top-1.5 h-3.5 w-3.5 rounded-full border border-neutral-700 bg-neutral-950" />
            <button
              type="button"
              onClick={() => onSelectNode?.(nodeId)}
              className="w-full rounded-md border border-neutral-800 bg-neutral-950/55 p-3 text-left transition hover:border-neutral-700 hover:bg-neutral-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent-300"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="truncate text-sm font-medium text-neutral-100">
                  {nodeDisplayName(nodeId)}
                </p>
                <StatusPill status={status} compact />
              </div>
              <p className="mt-2 font-mono text-[11px] text-neutral-500">
                {formatTimestamp(runNode?.completed_at ?? runNode?.started_at)}
              </p>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
