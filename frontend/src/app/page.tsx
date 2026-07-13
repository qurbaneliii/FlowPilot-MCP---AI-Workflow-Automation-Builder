"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorState } from "@/components/layout/ErrorState";
import { SectionCard } from "@/components/layout/SectionCard";
import { ContextPanel } from "@/components/workflow/ContextPanel";
import { StartWorkflowView } from "@/components/workflow/StartWorkflowView";
import { WorkflowCanvas } from "@/components/workflow/WorkflowCanvas";
import { WorkflowSummaryBar } from "@/components/workflow/WorkflowSummaryBar";
import { WorkspaceTabs } from "@/components/workflow/WorkspaceTabs";
import { GuidedStepper } from "@/components/workflow/GuidedStepper";
import { NextActionCard } from "@/components/workflow/NextActionCard";
import { useApprovalActions } from "@/hooks/useApprovalActions";
import { useRunPolling } from "@/hooks/useRunPolling";
import { useWorkflow } from "@/hooks/useWorkflow";
import { getHealth } from "@/lib/api";
import type { HealthResponse } from "@/types/api";

export default function HomePage() {
  const workflowState = useWorkflow();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const runState = useRunPolling({
    workflowId: workflowState.workflow?.workflow_id
  });
  const approvalActions = useApprovalActions({
    onSettled: runState.setRunFromAction
  });

  useEffect(() => {
    void getHealth()
      .then((response) => {
        setHealth(response);
        setHealthError(null);
      })
      .catch((error: unknown) => {
        setHealthError(
          error instanceof Error ? error.message : "Backend health check failed."
        );
      });
  }, []);

  const graph = workflowState.workflow?.workflow;
  const mode = runState.run?.mode;
  const activeSelectedNodeId =
    selectedNodeId ?? runState.run?.ui_state?.canvas_focus_node_id ?? null;

  return (
    <AppShell health={health} healthError={healthError} mode={mode}>
      {!workflowState.workflow ? (
        <StartWorkflowView
          prompt={workflowState.prompt}
          repoUrl={workflowState.repoUrl}
          validationErrors={workflowState.validationErrors}
          isGenerating={workflowState.isGenerating}
          error={workflowState.error}
          onPromptChange={workflowState.setPrompt}
          onRepoUrlChange={workflowState.setRepoUrl}
          onGenerate={() => {
            void workflowState.generate();
          }}
        />
      ) : (
        <div className="space-y-6">
          <GuidedStepper
            hasWorkflow
            runStatus={runState.run?.status}
            guidedSteps={runState.run?.guided_steps ?? workflowState.workflow.guided_steps}
          />
          <NextActionCard hasWorkflow run={runState.run} workflow={workflowState.workflow} />
          <WorkflowSummaryBar
            workflow={workflowState.workflow}
            graph={graph}
            run={runState.run}
            repoUrl={workflowState.repoUrl}
            mode={mode}
            isStarting={runState.isStarting}
            onRun={() => {
              void runState.startRun();
            }}
          />

          {runState.error && (
            <ErrorState title="Run failed" message={runState.error} />
          )}

          <section id="canvas" className="workspace-grid">
            <SectionCard
              title="Workflow Canvas"
              eyebrow="Main workspace"
              className="min-w-0"
            >
              <WorkflowCanvas
                graph={graph}
                workflow={workflowState.workflow}
                run={runState.run}
                isLoading={workflowState.isGenerating}
                selectedNodeId={activeSelectedNodeId}
                onSelectNode={setSelectedNodeId}
              />
            </SectionCard>

            <ContextPanel
              graph={graph}
              run={runState.run}
              mode={mode}
              selectedNodeId={activeSelectedNodeId}
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
            mode={mode}
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
      )}
    </AppShell>
  );
}
