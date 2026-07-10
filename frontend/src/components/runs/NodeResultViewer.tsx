import { EmptyState } from "@/components/layout/EmptyState";
import { StatusPill } from "@/components/layout/StatusPill";
import { pluralize, summarizeUnknown } from "@/lib/formatters";
import type { Run } from "@/types/run";
import { Boxes } from "lucide-react";

interface NodeResultViewerProps {
  run?: Run | null;
}

export function NodeResultViewer({ run }: NodeResultViewerProps) {
  if (!run?.nodes.length) {
    return (
      <EmptyState
        icon={Boxes}
        title="No node outputs yet"
        description="Completed node outputs will appear as compact, inspectable summaries."
      />
    );
  }
  return (
    <div className="grid gap-3 lg:grid-cols-2">
      {run.nodes.map((node) => (
        <div key={node.node_id} className="rounded-md border border-neutral-800 bg-neutral-950/55 p-3">
          <div className="mb-3 flex items-center justify-between gap-2">
            <p className="truncate text-sm font-medium text-neutral-100">
              {node.output_summary?.title ??
                run.node_results?.find((item) => item.node_id === node.node_id)?.title ??
                node.name ??
                node.node_id}
            </p>
            <StatusPill status={node.status} compact />
          </div>
          <p className="text-sm leading-6 text-neutral-400">
            {node.error
              ? String(node.error.message ?? "Node failed.")
              : node.output_summary?.summary ??
                run.node_results?.find((item) => item.node_id === node.node_id)?.summary ??
                summarizeNodeResult(node.node_id, node.output)}
          </p>
          {node.output && (
            <details className="mt-3 rounded-md border border-neutral-800 bg-neutral-950/70 p-3">
              <summary className="cursor-pointer text-xs font-medium text-neutral-400">
                Raw details
              </summary>
              <pre className="mt-3 max-h-64 overflow-auto text-xs leading-5 text-neutral-300">
                {JSON.stringify(node.output, null, 2)}
              </pre>
            </details>
          )}
        </div>
      ))}
    </div>
  );
}

function summarizeNodeResult(
  nodeId: string,
  output?: Record<string, unknown> | null
): string {
  if (!output) return "No output yet";
  if (nodeId === "manual_trigger") {
    const prompt = output.source_prompt ?? output.prompt;
    const repoUrl = output.repo_url;
    return `${typeof repoUrl === "string" ? repoUrl : "Repository captured"}${
      typeof prompt === "string" ? ` | ${prompt.slice(0, 90)}` : ""
    }`;
  }
  if (nodeId === "github_repo_reader") {
    const snapshot = asRecord(output.repo_snapshot);
    const entries = snapshot?.tree;
    const readme = snapshot?.readme;
    return `${Array.isArray(entries) ? pluralize(entries.length, "file") : "Repository snapshot"} scanned; README ${
      readme ? "found" : "not detected"
    }; mode ${String(output.mode ?? snapshot?.mode ?? "pending")}.`;
  }
  if (nodeId === "ai_repo_analyzer") {
    const findings = Array.isArray(output.findings) ? output.findings : [];
    const warningCount = findings.filter(
      (finding) => asRecord(finding)?.severity === "warning"
    ).length;
    const criticalCount = findings.filter(
      (finding) => asRecord(finding)?.severity === "critical"
    ).length;
    return `${pluralize(findings.length, "finding")} captured: ${warningCount} warning, ${criticalCount} critical.`;
  }
  if (nodeId === "readme_reviewer") {
    const missing = Array.isArray(output.missing_sections)
      ? output.missing_sections.length
      : 0;
    return `README score ${String(output.quality_score ?? "n/a")}; ${pluralize(missing, "missing section")}.`;
  }
  if (nodeId === "issue_draft_generator") {
    const drafts = Array.isArray(output.issue_drafts)
      ? output.issue_drafts
      : Array.isArray(output.issues)
        ? output.issues
        : [];
    return `${pluralize(drafts.length, "GitHub issue draft")} ready for approval.`;
  }
  if (nodeId === "human_approval") {
    return `${String(output.approval_summary ?? "Approval gate ready")} Risk level: ${String(output.risk_level ?? "medium")}.`;
  }
  if (nodeId === "github_issue_creator") {
    const created = Array.isArray(output.created_issues) ? output.created_issues : [];
    return `${pluralize(created.length, "issue")} ${created.length ? "created" : "skipped or pending"} in ${String(output.mode ?? "pending")} mode.`;
  }
  if (nodeId === "linkedin_draft_generator") {
    const draft = asRecord(output.linkedin_draft) ?? output;
    const hashtags = Array.isArray(draft.hashtags) ? draft.hashtags.length : 0;
    return `LinkedIn draft generated with ${pluralize(hashtags, "hashtag")}.`;
  }
  if (nodeId === "markdown_report_writer") {
    const artifacts = Array.isArray(output.artifacts) ? output.artifacts : [];
    return `${pluralize(artifacts.length, "artifact")} generated for review.`;
  }
  return summarizeUnknown(output);
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}
