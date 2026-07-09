"use client";

import { Handle, Position, type NodeProps } from "reactflow";
import { getNodeTypeMeta, getStatusMeta } from "@/lib/constants";
import type { FlowNodeData } from "@/lib/workflowMapper";

export function WorkflowNode({ data }: NodeProps<FlowNodeData>) {
  const typeMeta = getNodeTypeMeta(data.workflowNode.type);
  const statusMeta = getStatusMeta(data.status);
  const Icon = typeMeta.icon;
  const statusClass =
    data.status === "running"
      ? "node-running"
      : data.status === "completed"
        ? "node-completed"
        : data.status === "failed"
          ? "node-failed"
          : data.status === "waiting_for_approval"
            ? "node-approval"
            : data.status === "skipped"
              ? "node-skipped"
              : "";

  return (
    <div className={`workflow-node ${statusClass}`}>
      <Handle type="target" position={Position.Top} className="workflow-handle" />
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-md border border-neutral-700 bg-neutral-950">
            <Icon className={`h-4 w-4 ${typeMeta.accent}`} aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-neutral-50">
              {data.workflowNode.name}
            </p>
            <p className="truncate font-mono text-[11px] uppercase tracking-normal text-neutral-500">
              {typeMeta.label}
            </p>
          </div>
        </div>
        <span
          className={`mt-1 h-2 w-2 shrink-0 rounded-full ${statusMeta.dotClassName}`}
          aria-label={`Status: ${statusMeta.label}`}
        />
      </div>
      <div className="mt-3 rounded-md border border-neutral-800 bg-neutral-950/70 px-2.5 py-2">
        <p className="line-clamp-2 text-xs leading-5 text-neutral-400">
          {data.runNode?.error
            ? String(data.runNode.error.message ?? "Node failed.")
            : data.outputSummary}
        </p>
      </div>
      <Handle type="source" position={Position.Bottom} className="workflow-handle" />
    </div>
  );
}
