"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorState } from "@/components/layout/ErrorState";
import { SectionCard } from "@/components/layout/SectionCard";
import { RunStatusBadge } from "@/components/runs/RunStatusBadge";
import { ContextPanel } from "@/components/workflow/ContextPanel";
import { WorkflowCanvas } from "@/components/workflow/WorkflowCanvas";
import { WorkspaceTabs } from "@/components/workflow/WorkspaceTabs";
import { GuidedStepper } from "@/components/workflow/GuidedStepper";
import { NextActionCard } from "@/components/workflow/NextActionCard";
import { useApprovalActions } from "@/hooks/useApprovalActions";
import { useRunPolling } from "@/hooks/useRunPolling";
import { getHealth, getWorkflow } from "@/lib/api";
import { formatShortId } from "@/lib/formatters";
import { getWorkflowSummary } from "@/lib/workflowMapper";
import type { HealthResponse, Workflow } from "@/types/api";

export default function RunDetailPage() {
  const params = useParams<{ runId: string }>();
  const runId = params.runId;
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const runState = useRunPolling({ initialRunId: runId });
  const approvalActions = useApprovalActions({
    onSettled: runState.setRunFromAction
  });

  useEffect(() => {
    void getHealth()
      .then(setHealth)
      .catch((error: unknown) =>
        setHealthError(
          error instanceof Error ? error.message : "Backend health check failed."
        )
      );
  }, []);

  useEffect(() => {
    if (!runState.run?.workflow_id) return;
    void getWorkflow(runState.run.workflow_id)
      .then(setWorkflow)
      .catch((error: unknown) =>
        setWorkflowError(
          error instanceof Error ? error.message : "Workflow lookup failed."
        )
      );
  }, [runState.run?.workflow_id]);

  const graph = workflow?.workflow;
  const summary = getWorkflowSummary(graph);

  return (
    <AppShell health={health} healthError={healthError} mode={runState.run?.mode}>
      <div className="space-y-6">
        <GuidedStepper hasWorkflow runStatus={runState.run?.status} />
        <NextActionCard hasWorkflow run={runState.run} />
        <section className="summary-bar">
          <div>
            <p className="kicker">Run detail</p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <h2 className="text-xl font-semibold text-neutral-50">
                {summary.name}
              </h2>
              <RunStatusBadge status={runState.run?.status ?? "pending"} />
            </div>
            <p className="mt-2 text-sm text-neutral-400">
              Run {formatShortId(runId)} | {summary.nodeCount} nodes |{" "}
              {runState.run?.mode ?? "mode pending"}
            </p>
          </div>
        </section>

        {runState.error && (
          <ErrorState title="Run lookup failed" message={runState.error} />
        )}
        {workflowError && (
          <ErrorState title="Workflow lookup failed" message={workflowError} />
        )}

        <section id="canvas" className="workspace-grid">
          <SectionCard title="Workflow Canvas" eyebrow="Main workspace">
            <WorkflowCanvas
              graph={graph}
              run={runState.run}
              selectedNodeId={selectedNodeId}
              onSelectNode={setSelectedNodeId}
            />
          </SectionCard>
          <ContextPanel
            graph={graph}
            run={runState.run}
            mode={runState.run?.mode}
            selectedNodeId={selectedNodeId}
            loadingDecision={approvalActions.loadingDecision}
            approvalError={approvalActions.error}
            lastDecision={approvalActions.lastDecision}
            onSelectNode={setSelectedNodeId}
            onApprove={(approvalId) => {
              void approvalActions.approve(approvalId);
            }}
            onReject={(approvalId) => {
              void approvalActions.reject(approvalId);
            }}
          />
        </section>

        <WorkspaceTabs
          graph={graph}
          run={runState.run}
          mode={runState.run?.mode}
          loadingDecision={approvalActions.loadingDecision}
          approvalError={approvalActions.error}
          lastDecision={approvalActions.lastDecision}
          onSelectNode={setSelectedNodeId}
          onApprove={(approvalId) => {
            void approvalActions.approve(approvalId);
          }}
          onReject={(approvalId) => {
            void approvalActions.reject(approvalId);
          }}
        />
      </div>
    </AppShell>
  );
}
