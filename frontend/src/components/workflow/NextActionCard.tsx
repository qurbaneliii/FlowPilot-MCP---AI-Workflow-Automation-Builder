import { ArrowRight, Loader2 } from "lucide-react";
import type { Run } from "@/types/run";
import type { GeneratedWorkflow } from "@/types/workflow";

interface NextActionCardProps {
  hasWorkflow?: boolean;
  run?: Run | null;
  workflow?: GeneratedWorkflow | null;
}

export function NextActionCard({ hasWorkflow = false, run, workflow }: NextActionCardProps) {
  const guidance = getGuidance(hasWorkflow, run, workflow);
  return (
    <aside className={`next-action-card next-action-${guidance.tone}`} aria-live="polite">
      <span className="next-action-icon">
        {guidance.tone === "running" ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        )}
      </span>
      <div>
        <p className="font-mono text-[11px] uppercase text-neutral-500">Next best action</p>
        <p className="mt-1 text-sm font-semibold leading-6 text-neutral-100">{guidance.title}</p>
        <p className="text-sm leading-6 text-neutral-400">{guidance.text}</p>
      </div>
    </aside>
  );
}

function getGuidance(hasWorkflow: boolean, run?: Run | null, workflow?: GeneratedWorkflow | null) {
  const structuredAction = run?.next_action ?? workflow?.next_action;
  if (structuredAction) {
    return {
      title: structuredAction.title,
      text: structuredAction.description,
      tone:
        structuredAction.severity === "error"
          ? "error"
          : structuredAction.severity === "warning"
            ? "approval"
            : run?.status === "completed"
              ? "success"
              : run && run.status !== "waiting_for_approval"
                ? "running"
                : "default"
    };
  }
  const backendAction = run?.summary?.next_required_action;
  if (!hasWorkflow) {
    return { title: "Define the automation", text: "Enter a GitHub repository URL and generate the workflow.", tone: "default" };
  }
  if (!run) {
    return { title: "Run the automation", text: "Review the generated workflow, then run the automation.", tone: "default" };
  }
  if (run.status === "waiting_for_approval") {
    return { title: "Human approval required", text: "Review the issue drafts, then approve or skip GitHub issue creation.", tone: "approval" };
  }
  if (run.status === "completed") {
    return { title: "Review generated outputs", text: "Review the generated reports and copy the LinkedIn draft.", tone: "success" };
  }
  if (run.status === "failed") {
    return { title: "Inspect failed node", text: "Open Logs to inspect the failed node and its recovery guidance.", tone: "error" };
  }
  return {
    title: "Workflow is running",
    text: backendAction ?? "FlowPilot is reading the repository and executing workflow nodes.",
    tone: "running"
  };
}
