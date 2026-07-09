import { Clock3, FileText, GitBranch, ShieldAlert } from "lucide-react";
import { RunStatusBadge } from "./RunStatusBadge";
import { formatShortId, formatTimestamp } from "@/lib/formatters";
import type { Run } from "@/types/run";

interface RunSummaryPanelProps {
  run?: Run | null;
}

export function RunSummaryPanel({ run }: RunSummaryPanelProps) {
  if (!run) {
    return (
      <div className="rounded-md border border-neutral-800 bg-neutral-950/60 p-4 text-sm text-neutral-400">
        Start a run to see execution state, approval mode, and artifact counts.
      </div>
    );
  }
  const completed = run.nodes.filter((node) => node.status === "completed").length;
  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-normal text-neutral-500">
            Run {formatShortId(run.run_id)}
          </p>
          <h3 className="mt-1 text-sm font-semibold text-neutral-50">
            Workflow execution
          </h3>
        </div>
        <RunStatusBadge status={run.status} />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <Metric icon={GitBranch} label="Nodes complete" value={`${completed}/${run.nodes.length}`} />
        <Metric icon={ShieldAlert} label="Mode" value={run.mode ?? "pending"} />
        <Metric icon={FileText} label="Artifacts" value={String(run.artifacts.length)} />
        <Metric icon={Clock3} label="Started" value={formatTimestamp(run.started_at)} />
      </div>
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value
}: {
  icon: typeof Clock3;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md border border-neutral-800 bg-neutral-950/55 p-3">
      <div className="flex items-center gap-2 text-xs text-neutral-500">
        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
        {label}
      </div>
      <p className="mt-2 truncate text-sm font-medium text-neutral-100">{value}</p>
    </div>
  );
}
