import { ArrowRight, Loader2 } from "lucide-react";
import type { Run } from "@/types/run";

interface NextActionCardProps {
  hasWorkflow?: boolean;
  run?: Run | null;
}

export function NextActionCard({ hasWorkflow = false, run }: NextActionCardProps) {
  const guidance = getGuidance(hasWorkflow, run);
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
        <p className="mt-1 text-sm font-medium leading-6 text-neutral-100">{guidance.text}</p>
      </div>
    </aside>
  );
}

function getGuidance(hasWorkflow: boolean, run?: Run | null) {
  const backendAction = run?.summary?.next_required_action;
  if (!hasWorkflow) {
    return { text: "Enter a GitHub repository URL and generate the workflow.", tone: "default" };
  }
  if (!run) {
    return { text: "Review the generated workflow, then run the automation.", tone: "default" };
  }
  if (run.status === "waiting_for_approval") {
    return { text: "Review the issue drafts, then approve or skip GitHub issue creation.", tone: "approval" };
  }
  if (run.status === "completed") {
    return { text: "Review the generated reports and copy the LinkedIn draft.", tone: "success" };
  }
  if (run.status === "failed") {
    return { text: "Open Logs to inspect the failed node and its recovery guidance.", tone: "error" };
  }
  return {
    text: backendAction ?? "FlowPilot is reading the repository and executing workflow nodes.",
    tone: "running"
  };
}
