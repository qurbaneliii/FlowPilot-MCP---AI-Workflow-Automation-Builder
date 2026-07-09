"use client";

import { useEffect, useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  ReactFlowProvider,
  useReactFlow,
  type Node
} from "reactflow";
import { EmptyState } from "@/components/layout/EmptyState";
import { WorkflowNode } from "./WorkflowNode";
import { mapWorkflowToReactFlow, type FlowNodeData } from "@/lib/workflowMapper";
import type { Run } from "@/types/run";
import type { WorkflowGraph } from "@/types/workflow";
import { Crosshair, GitBranch, Maximize2 } from "lucide-react";

interface WorkflowCanvasProps {
  graph?: WorkflowGraph | null;
  run?: Run | null;
  isLoading?: boolean;
  selectedNodeId?: string | null;
  onSelectNode?: (nodeId: string | null) => void;
}

const nodeTypes = { flowpilotNode: WorkflowNode };

export function WorkflowCanvas(props: WorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <WorkflowCanvasInner {...props} />
    </ReactFlowProvider>
  );
}

function WorkflowCanvasInner({
  graph,
  run,
  isLoading = false,
  selectedNodeId,
  onSelectNode
}: WorkflowCanvasProps) {
  const { fitView } = useReactFlow();
  const [internalSelectedNodeId, setInternalSelectedNodeId] = useState<string | null>(null);
  const activeSelectedNodeId = selectedNodeId ?? internalSelectedNodeId;
  const mapped = useMemo(() => mapWorkflowToReactFlow(graph, run), [graph, run]);
  const statusSummary = useMemo(() => {
    const statuses = new Map<string, number>();
    mapped.nodes.forEach((node) => {
      statuses.set(node.data.status, (statuses.get(node.data.status) ?? 0) + 1);
    });
    return statuses;
  }, [mapped.nodes]);
  const statusSignature = mapped.nodes
    .map((node) => `${node.id}:${node.data.status}`)
    .join("|");

  useEffect(() => {
    if (!mapped.nodes.length) return;
    const frame = requestAnimationFrame(() => {
      fitView({ padding: 0.14, duration: 450 });
    });
    return () => cancelAnimationFrame(frame);
  }, [fitView, mapped.nodes.length, statusSignature]);

  function centerGraph() {
    fitView({ padding: 0.14, duration: 350 });
  }

  if (isLoading) {
    return (
      <div className="canvas-shell grid min-h-[520px] place-items-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-pulse rounded-md border border-status-running/40 bg-status-running/10" />
          <h3 className="text-sm font-semibold text-neutral-100">Generating workflow graph</h3>
          <p className="mt-2 max-w-sm text-sm leading-6 text-neutral-400">
            FlowPilot is planning nodes, dependencies, approval gates, and report outputs.
          </p>
        </div>
      </div>
    );
  }

  if (!mapped.nodes.length) {
    return (
      <div className="canvas-shell">
        <EmptyState
          icon={GitBranch}
          title="No workflow graph yet"
          description="Generate an executable workflow to inspect nodes, edges, approval gates, and output stages."
        />
      </div>
    );
  }

  return (
    <div className="canvas-shell">
      <div className="canvas-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-400">
          <span>{mapped.nodes.length} nodes</span>
          {[...statusSummary.entries()].map(([status, count]) => (
            <span key={status} className="rounded-md border border-neutral-800 bg-neutral-950/70 px-2 py-1">
              {count} {status.replaceAll("_", " ")}
            </span>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button type="button" className="btn-ghost" onClick={centerGraph}>
            <Crosshair className="h-4 w-4" aria-hidden="true" />
            Center graph
          </button>
          <button type="button" className="btn-ghost" onClick={centerGraph}>
            <Maximize2 className="h-4 w-4" aria-hidden="true" />
            Fit view
          </button>
        </div>
      </div>
      <ReactFlow
        nodes={mapped.nodes.map((node): Node<FlowNodeData> => ({
          ...node,
          selected: node.id === activeSelectedNodeId
        }))}
        edges={mapped.edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.35}
        maxZoom={1.35}
        onNodeClick={(_, node) => {
          setInternalSelectedNodeId(node.id);
          onSelectNode?.(node.id);
        }}
        onPaneClick={() => {
          setInternalSelectedNodeId(null);
          onSelectNode?.(null);
        }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#25302d" gap={28} size={1} />
        <Controls className="flow-controls" />
      </ReactFlow>
    </div>
  );
}
