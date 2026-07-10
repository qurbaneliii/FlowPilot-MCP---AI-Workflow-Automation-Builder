"use client";

import { useMemo, useState } from "react";
import { GitHubAuditViewer } from "./GitHubAuditViewer";
import { IssueDraftsViewer } from "./IssueDraftsViewer";
import { LinkedInDraftViewer } from "./LinkedInDraftViewer";
import { MarkdownArtifactViewer } from "./MarkdownArtifactViewer";
import {
  extractAudit,
  extractIssueDrafts,
  extractLinkedInDraft
} from "@/lib/workflowMapper";
import type { Artifact } from "@/types/artifact";
import type { Run } from "@/types/run";

interface OutputReportsPanelProps {
  run?: Run | null;
}

const tabs = [
  { id: "audit", label: "Repo Audit Report" },
  { id: "readme", label: "README Improvement Plan" },
  { id: "issues", label: "GitHub Issue Drafts" },
  { id: "linkedin", label: "LinkedIn Draft" }
] as const;

type TabId = (typeof tabs)[number]["id"];

export function OutputReportsPanel({ run }: OutputReportsPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("audit");
  const artifactByType = useMemo(
    () =>
      new Map(
        (run?.artifacts ?? []).map((artifact) => [
          artifact.artifact_type,
          artifact
        ])
      ),
    [run?.artifacts]
  );
  const isAvailable = (artifactType: string) =>
    run?.artifact_tabs?.[artifactType]?.available ??
    artifactByType.has(artifactType);
  const audit = extractAudit(run);
  const issueDrafts = extractIssueDrafts(run);
  const linkedinDraft = extractLinkedInDraft(run);
  return (
    <div>
      <div className="mb-4 flex gap-2 overflow-x-auto rounded-md border border-neutral-800 bg-neutral-950/55 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`shrink-0 rounded-md px-3 py-2 text-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent-300 ${
              activeTab === tab.id
                ? "bg-neutral-800 text-neutral-50"
                : "text-neutral-400 hover:text-neutral-100"
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {activeTab === "audit" && (
        <div className="space-y-4">
          {(audit || !isAvailable("repo_audit_report")) && (
            <GitHubAuditViewer audit={audit} />
          )}
          {isAvailable("repo_audit_report") && (
            <MarkdownArtifactViewer
              artifact={artifactByType.get("repo_audit_report") as Artifact | undefined}
              fallbackTitle="Repo Audit Report"
            />
          )}
        </div>
      )}
      {activeTab === "readme" && (
        <MarkdownArtifactViewer
          artifact={artifactByType.get("readme_improvement_plan") as Artifact | undefined}
          fallbackTitle="README Improvement Plan"
        />
      )}
      {activeTab === "issues" && (
        <div className="space-y-4">
          {(issueDrafts.length > 0 || !isAvailable("github_issue_drafts")) && (
            <IssueDraftsViewer issues={issueDrafts} />
          )}
          {isAvailable("github_issue_drafts") && (
            <MarkdownArtifactViewer
              artifact={artifactByType.get("github_issue_drafts") as Artifact | undefined}
              fallbackTitle="GitHub Issue Drafts"
            />
          )}
        </div>
      )}
      {activeTab === "linkedin" && (
        <div className="space-y-4">
          {(linkedinDraft || !isAvailable("linkedin_post_draft")) && (
            <LinkedInDraftViewer draft={linkedinDraft} />
          )}
          {isAvailable("linkedin_post_draft") && (
            <MarkdownArtifactViewer
              artifact={artifactByType.get("linkedin_post_draft") as Artifact | undefined}
              fallbackTitle="LinkedIn Draft"
            />
          )}
        </div>
      )}
    </div>
  );
}
