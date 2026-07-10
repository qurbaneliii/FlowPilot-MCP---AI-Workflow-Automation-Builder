import { Github, Play, ShieldCheck } from "lucide-react";
import { RunStatusBadge } from "@/components/runs/RunStatusBadge";
import { StatusPill } from "@/components/layout/StatusPill";
import { getWorkflowSummary } from "@/lib/workflowMapper";
import { titleCase } from "@/lib/formatters";
import type { Run } from "@/types/run";
import type { GeneratedWorkflow, WorkflowGraph } from "@/types/workflow";

interface WorkflowSummaryBarProps {
  workflow?: GeneratedWorkflow | null;
  graph?: WorkflowGraph | null;
  run?: Run | null;
  repoUrl: string;
  mode?: string | null;
  isStarting?: boolean;
  onRun: () => void;
}

export function WorkflowSummaryBar({
  workflow,
  graph,
  run,
  repoUrl,
  mode,
  isStarting,
  onRun
}: WorkflowSummaryBarProps) {
  const summary = getWorkflowSummary(graph, workflow);
  return (
    <section className="summary-bar">
      <div className="min-w-0">
        <p className="kicker">Active workflow</p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h2 className="text-xl font-semibold text-neutral-50">{summary.name}</h2>
          <StatusPill status={workflow?.validation.valid ? "completed" : "pending"} label={summary.statusLabel ?? "Validated"} />
          {run && <RunStatusBadge status={run.status} />}
        </div>
        <div className="mt-3 flex flex-wrap gap-2 text-sm text-neutral-400">
          <span className="inline-flex items-center gap-1.5">
            <Github className="h-4 w-4 text-neutral-500" aria-hidden="true" />
            {(summary.repoUrl ?? repoUrl).replace("https://github.com/", "github.com/")}
          </span>
          <span>{summary.nodeCount} nodes</span>
          <span>{summary.riskyActionCount} risky action</span>
          <span>{summary.approvalRequired ? "Approval required" : "No approval gate"}</span>
          <span>{titleCase(summary.mode ?? mode ?? "mode pending")}</span>
        </div>
      </div>
      <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
        <button
          type="button"
          className="btn-secondary"
          disabled={!workflow || isStarting}
          onClick={onRun}
        >
          <Play className="h-4 w-4" aria-hidden="true" />
          {run ? "Run again" : isStarting ? "Starting..." : "Run workflow"}
        </button>
        <a href="#reports" className="btn-ghost">
          <ShieldCheck className="h-4 w-4" aria-hidden="true" />
          View reports
        </a>
      </div>
    </section>
  );
}
