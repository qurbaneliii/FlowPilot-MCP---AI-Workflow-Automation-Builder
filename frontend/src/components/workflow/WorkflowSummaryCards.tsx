import { AlertTriangle, CheckCircle2, GitBranch, Layers3 } from "lucide-react";
import { getWorkflowSummary } from "@/lib/workflowMapper";
import type { WorkflowGraph } from "@/types/workflow";

interface WorkflowSummaryCardsProps {
  graph?: WorkflowGraph | null;
}

export function WorkflowSummaryCards({ graph }: WorkflowSummaryCardsProps) {
  const summary = getWorkflowSummary(graph);
  const cards = [
    { label: "Workflow nodes", value: summary.nodeCount, icon: GitBranch },
    { label: "Estimated stages", value: summary.estimatedStages, icon: Layers3 },
    { label: "Risky actions", value: summary.riskyActionCount, icon: AlertTriangle },
    {
      label: "Approval gate",
      value: summary.approvalRequired ? "Required" : "Not needed",
      icon: CheckCircle2
    }
  ];
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.label} className="rounded-md border border-neutral-800 bg-neutral-900/70 p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-neutral-400">{card.label}</p>
              <Icon className="h-4 w-4 text-accent-300" aria-hidden="true" />
            </div>
            <p className="mt-2 text-xl font-semibold text-neutral-50">{card.value}</p>
          </div>
        );
      })}
    </div>
  );
}
