"use client";

import { useState } from "react";
import { Copy, PenLine } from "lucide-react";
import { EmptyState } from "@/components/layout/EmptyState";
import { copyToClipboard } from "@/lib/formatters";
import type { LinkedInDraft } from "@/types/artifact";

interface LinkedInDraftViewerProps {
  draft?: LinkedInDraft | null;
}

export function LinkedInDraftViewer({ draft }: LinkedInDraftViewerProps) {
  const [copied, setCopied] = useState(false);
  if (!draft) {
    return (
      <EmptyState
        icon={PenLine}
        title="No LinkedIn draft yet"
        description="FlowPilot generates draft copy only; it never publishes social posts."
      />
    );
  }
  const text = `${draft.post_text}\n\n${draft.hashtags.join(" ")}`;
  return (
    <article className="rounded-md border border-neutral-800 bg-neutral-950/55 p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-normal text-neutral-500">
            Draft, not published
          </p>
          <h3 className="mt-1 text-sm font-semibold text-neutral-50">
            LinkedIn demo post
          </h3>
        </div>
        <button
          type="button"
          className="btn-ghost"
          onClick={() => {
            void copyToClipboard(text).then(() => {
              setCopied(true);
              window.setTimeout(() => setCopied(false), 1200);
            });
          }}
        >
          <Copy className="h-4 w-4" aria-hidden="true" />
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <p className="whitespace-pre-wrap text-sm leading-7 text-neutral-200">
        {draft.post_text}
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {draft.hashtags.map((tag) => (
          <span key={tag} className="rounded-md border border-accent-500/30 bg-accent-500/10 px-2 py-1 text-xs text-accent-200">
            {tag}
          </span>
        ))}
      </div>
      <p className="mt-4 text-xs text-neutral-500">Tone: {draft.tone}</p>
    </article>
  );
}
