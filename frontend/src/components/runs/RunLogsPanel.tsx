"use client";

import { useMemo, useState } from "react";
import { ChevronDown, Terminal } from "lucide-react";
import { formatTimestamp, summarizeUnknown } from "@/lib/formatters";
import type { Run, RunLog } from "@/types/run";

interface RunLogsPanelProps {
  run?: Run | null;
}

export function RunLogsPanel({ run }: RunLogsPanelProps) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const logs = useMemo(() => normalizeLogs(run), [run]);
  if (!run) {
    return (
      <div className="rounded-md border border-neutral-800 bg-neutral-950/60 p-4 text-sm text-neutral-400">
        Execution logs will appear after you run the workflow.
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {logs.map((entry) => (
        <div
          key={`${entry.node_id}-${entry.message}`}
          className="rounded-md border border-neutral-800 bg-neutral-950/55"
        >
          <button
            type="button"
            onClick={() =>
              setExpanded((current) => {
                const nextId = entry.node_id ?? entry.message ?? "run-log";
                return current === nextId ? null : nextId;
              })
            }
            className="flex w-full items-center justify-between gap-3 p-3 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent-300"
          >
            <span className="flex min-w-0 items-center gap-2">
              <Terminal className="h-4 w-4 shrink-0 text-neutral-500" aria-hidden="true" />
              <span className="truncate text-sm text-neutral-100">{entry.message}</span>
            </span>
            <span className="flex shrink-0 items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  entry.severity === "error"
                    ? "bg-status-danger"
                    : entry.severity === "warning"
                      ? "bg-status-warning"
                      : "bg-neutral-600"
                }`}
                aria-label={`Severity: ${entry.severity ?? "info"}`}
              />
              <ChevronDown className="h-4 w-4 text-neutral-500" aria-hidden="true" />
            </span>
          </button>
          {expanded === (entry.node_id ?? entry.message ?? "run-log") && (
            <div className="border-t border-neutral-800 p-3">
              <p className="font-mono text-[11px] text-neutral-500">
                {formatTimestamp(entry.timestamp)}
              </p>
              <p className="mt-2 text-xs font-medium text-neutral-400">Technical details</p>
              <pre className="mt-2 max-h-56 overflow-auto rounded-md bg-neutral-950 p-3 text-xs leading-5 text-neutral-300">
                {JSON.stringify(entry.details ?? {}, null, 2)}
              </pre>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function normalizeLogs(run?: Run | null): RunLog[] {
  if (!run) return [];
  if (run.logs.length) return run.logs;
  if (run.timeline?.length) {
    return run.timeline.map((entry) => ({
      timestamp: entry.timestamp ?? undefined,
      node_id: entry.node_id,
      severity: entry.severity ?? "info",
      message: entry.message,
      details: {
        status: entry.status,
        node: entry.name
      }
    }));
  }
  return run.nodes.map((node) => ({
    timestamp: node.completed_at ?? node.started_at ?? undefined,
    node_id: node.node_id,
    severity: node.status === "failed" ? "error" : "info",
    message:
      node.status === "failed"
        ? `${node.node_id} failed`
        : `${node.node_id} ${node.status}`,
    details: {
      status: node.status,
      output: summarizeUnknown(node.output),
      error: node.error
    }
  }));
}
