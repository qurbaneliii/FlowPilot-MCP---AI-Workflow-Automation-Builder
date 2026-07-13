import { Github } from "lucide-react";
import { EmptyState } from "@/components/layout/EmptyState";
import { StatusPill } from "@/components/layout/StatusPill";
import { CopyButton } from "@/components/layout/CopyButton";
import type { IssueDraft } from "@/types/artifact";

interface IssueDraftsViewerProps {
  issues: IssueDraft[];
  artifactContent?: string;
}

export function IssueDraftsViewer({ issues, artifactContent }: IssueDraftsViewerProps) {
  if (!issues.length) {
    return (
      <EmptyState
        icon={Github}
        title="No GitHub issue drafts yet"
        description="Warning and critical audit findings will become reviewable issue draft cards."
      />
    );
  }
  return (
    <div className="space-y-3">
      {artifactContent && <div className="flex justify-end"><CopyButton value={artifactContent} label="Copy issue drafts" /></div>}
      <div className="grid gap-3 lg:grid-cols-2">
      {issues.map((issue) => (
        <article key={issue.title} className="rounded-md border border-neutral-800 bg-neutral-950/55 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-normal text-neutral-500">
                Priority {issue.priority}
              </p>
              <h3 className="mt-1 text-sm font-semibold text-neutral-50">{issue.title}</h3>
            </div>
            <StatusPill status={issue.created ? "completed" : "pending"} label={issue.created ? "Created" : "Draft"} />
          </div>
          <p className="mt-3 line-clamp-4 text-sm leading-6 text-neutral-300">{issue.body}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {issue.labels.map((label) => (
              <span key={label} className="rounded-md border border-neutral-800 bg-neutral-900 px-2 py-1 text-xs text-neutral-300">
                {label}
              </span>
            ))}
          </div>
          {issue.acceptance_criteria.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-xs font-medium uppercase tracking-normal text-neutral-500">
                Acceptance criteria
              </p>
              <ul className="space-y-1 text-sm text-neutral-300">
                {issue.acceptance_criteria.map((item) => (
                  <li key={item}>- {item}</li>
                ))}
              </ul>
            </div>
          )}
          {(issue.display_url || issue.url) && (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-neutral-800 pt-3">
              <p className="break-all font-mono text-xs text-accent-300">{issue.display_url ?? issue.url}</p>
              <CopyButton value={issue.display_url ?? issue.url ?? ""} label="Copy URL" />
            </div>
          )}
        </article>
      ))}
      </div>
    </div>
  );
}
