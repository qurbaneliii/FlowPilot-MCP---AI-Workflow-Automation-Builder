import { CheckCircle2, FileText, Github, PenLine, RotateCcw } from "lucide-react";
import Link from "next/link";
import { CopyButton } from "@/components/layout/CopyButton";
import { extractLinkedInDraft } from "@/lib/workflowMapper";
import type { Run } from "@/types/run";

export function CompletionSummary({ run, lastDecision }: { run: Run; lastDecision?: string | null }) {
  const linkedin = extractLinkedInDraft(run);
  const linkedinText = linkedin ? `${linkedin.post_text}\n\n${linkedin.hashtags.join(" ")}` : "";
  const issueNode = run.nodes.find((node) => node.node_id === "github_issue_creator");
  const issueMode = String(issueNode?.output?.mode ?? run.mode ?? "mock");
  const issueCount = Array.isArray(issueNode?.output?.created_issues) ? issueNode.output.created_issues.length : 0;
  const backendSummary = run.completion_summary;
  const deliverables = backendSummary?.primary_outputs?.length
    ? backendSummary.primary_outputs.map((output) => output.label)
    : ["Repo Audit Report", "README Improvement Plan", "GitHub Issue Drafts", "LinkedIn Draft"];
  const deliverableIcons = {
    "GitHub Issue Drafts": Github,
    "LinkedIn Draft": PenLine
  } as const;

  return (
    <div className="space-y-4">
      <div className="completion-hero">
        <CheckCircle2 className="h-8 w-8 text-status-success" aria-hidden="true" />
        <div>
          <p className="kicker">{backendSummary?.title ?? "Workflow completed"}</p>
          <h3 className="mt-1 text-xl font-semibold text-neutral-50">Your repository audit is ready.</h3>
          <p className="mt-2 text-sm leading-6 text-neutral-300">
            {backendSummary?.description ?? `FlowPilot completed all ${run.summary?.nodes_total ?? run.nodes.length} workflow nodes and generated ${run.artifacts.length} deliverables.`}
          </p>
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {deliverables.map((label) => {
          const Icon = deliverableIcons[label as keyof typeof deliverableIcons] ?? FileText;
          return <div key={label} className="deliverable-chip">
            <Icon className="h-4 w-4 text-accent-300" aria-hidden="true" />
            {label}
          </div>;
        })}
      </div>
      <div className="rounded-md border border-neutral-800 bg-neutral-950/60 p-3 text-sm leading-6 text-neutral-300">
        {backendSummary?.issue_creation.message ?? (lastDecision === "rejected"
          ? "Issue creation was skipped by your decision. Safe reports were still generated."
          : issueMode === "mock"
            ? `Issue creation ran in safe mock mode (${issueCount} simulated result). No real GitHub issues were created.`
            : `${issueCount} GitHub issue${issueCount === 1 ? " was" : "s were"} created after approval.`)}
      </div>
      <div className="flex flex-wrap gap-2">
        <a href="#reports" className="btn-primary">View reports</a>
        {linkedinText && <CopyButton value={linkedinText} label="Copy LinkedIn draft" />}
        <Link href="/" className="btn-ghost"><RotateCcw className="h-4 w-4" aria-hidden="true" />Start another workflow</Link>
      </div>
    </div>
  );
}
