import { AlertTriangle, BarChart3, ShieldCheck } from "lucide-react";
import { EmptyState } from "@/components/layout/EmptyState";
import { StatusPill } from "@/components/layout/StatusPill";
import { titleCase } from "@/lib/formatters";
import type { GitHubAudit } from "@/types/artifact";

interface GitHubAuditViewerProps {
  audit?: GitHubAudit | null;
}

export function GitHubAuditViewer({ audit }: GitHubAuditViewerProps) {
  if (!audit) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title="No repository audit yet"
        description="The audit viewer will show findings, severity, affected files, and issue recommendations after the analyzer runs."
      />
    );
  }
  const severityCounts = audit.findings.reduce<Record<string, number>>(
    (counts, finding) => ({
      ...counts,
      [finding.severity]: (counts[finding.severity] ?? 0) + 1
    }),
    {}
  );
  const categories = [...new Set(audit.findings.map((finding) => finding.category))];
  return (
    <div className="space-y-4">
      <div className="rounded-md border border-neutral-800 bg-neutral-950/55 p-4">
        <div className="flex items-start gap-3">
          <BarChart3 className="mt-1 h-5 w-5 shrink-0 text-accent-300" aria-hidden="true" />
          <div>
            <h3 className="text-sm font-semibold text-neutral-50">Overall summary</h3>
            <p className="mt-2 text-sm leading-6 text-neutral-300">{audit.summary}</p>
          </div>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {["info", "warning", "critical"].map((severity) => (
          <div key={severity} className="rounded-md border border-neutral-800 bg-neutral-950/55 p-3">
            <p className="font-mono text-[11px] uppercase tracking-normal text-neutral-500">
              {severity}
            </p>
            <p className="mt-1 text-xl font-semibold text-neutral-50">
              {severityCounts[severity] ?? 0}
            </p>
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => (
          <span
            key={category}
            className="rounded-md border border-neutral-800 bg-neutral-950 px-2.5 py-1.5 text-xs text-neutral-300"
          >
            {titleCase(category)}
          </span>
        ))}
      </div>
      {audit.risk_flags.length > 0 && (
        <div className="rounded-md border border-status-warning/40 bg-status-warning/10 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-status-warning">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" />
            Risk flags
          </div>
          <div className="space-y-2">
            {audit.risk_flags.map((flag) => (
              <div key={flag.code} className="flex items-start justify-between gap-3 text-sm">
                <div>
                  <p className="font-mono text-xs text-neutral-200">{flag.code}</p>
                  <p className="mt-1 leading-6 text-neutral-300">{flag.description}</p>
                </div>
                <StatusPill
                  status={flag.severity === "critical" ? "failed" : "waiting_for_approval"}
                  label={titleCase(flag.severity)}
                  compact
                />
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="space-y-3">
        {audit.findings.map((finding) => (
          <article key={`${finding.category}-${finding.title}`} className="rounded-md border border-neutral-800 bg-neutral-950/55 p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-mono text-[11px] uppercase tracking-normal text-neutral-500">
                  {titleCase(finding.category)}
                </p>
                <h4 className="mt-1 text-sm font-semibold text-neutral-50">
                  {finding.title}
                </h4>
              </div>
              <StatusPill status={finding.severity === "critical" ? "failed" : finding.severity === "warning" ? "waiting_for_approval" : "completed"} label={titleCase(finding.severity)} />
            </div>
            <p className="mt-3 text-sm leading-6 text-neutral-300">{finding.description}</p>
            <p className="mt-2 text-sm leading-6 text-neutral-400">
              Recommendation: {finding.recommendation}
            </p>
            {finding.affected_files.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {finding.affected_files.map((file) => (
                  <span key={file} className="rounded-md bg-neutral-900 px-2 py-1 font-mono text-[11px] text-neutral-300">
                    {file}
                  </span>
                ))}
              </div>
            )}
            {finding.suggested_issue_title && (
              <p className="mt-3 text-xs text-accent-300">
                Suggested issue: {finding.suggested_issue_title}
              </p>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
