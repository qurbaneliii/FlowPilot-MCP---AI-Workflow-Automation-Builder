"use client";

import { useState } from "react";
import { Copy, FileText } from "lucide-react";
import { copyToClipboard, formatTimestamp } from "@/lib/formatters";
import type { Artifact } from "@/types/artifact";

interface MarkdownArtifactViewerProps {
  artifact?: Artifact | null;
  fallbackTitle: string;
}

export function MarkdownArtifactViewer({
  artifact,
  fallbackTitle
}: MarkdownArtifactViewerProps) {
  const [copied, setCopied] = useState(false);
  if (!artifact) {
    return (
      <div className="rounded-md border border-dashed border-neutral-800 bg-neutral-950/55 p-6 text-sm text-neutral-400">
        {fallbackTitle} has not been generated yet.
      </div>
    );
  }
  return (
    <article className="rounded-md border border-neutral-800 bg-neutral-950/55">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-800 p-4">
        <div className="flex min-w-0 items-center gap-2">
          <FileText className="h-4 w-4 shrink-0 text-accent-300" aria-hidden="true" />
          <div className="min-w-0">
            <h3 className="truncate text-sm font-semibold text-neutral-50">
              {artifact.filename}
            </h3>
            <p className="font-mono text-[11px] text-neutral-500">
              {artifact.artifact_type} | {formatTimestamp(artifact.created_at)} |{" "}
              {artifact.mode ?? "mode pending"}
            </p>
          </div>
        </div>
        <button
          type="button"
          className="btn-ghost"
          onClick={() => {
            void copyToClipboard(artifact.content).then(() => {
              setCopied(true);
              window.setTimeout(() => setCopied(false), 1200);
            });
          }}
        >
          <Copy className="h-4 w-4" aria-hidden="true" />
          {copied ? "Copied" : "Copy"}
        </button>
      </header>
      <div className="markdown-viewer p-4">{renderMarkdown(artifact.content)}</div>
    </article>
  );
}

function renderMarkdown(content: string) {
  return content.split("\n").map((line, index) => {
    const key = `${index}-${line}`;
    if (line.startsWith("# ")) {
      return (
        <h2 key={key} className="mb-3 mt-1 text-lg font-semibold text-neutral-50">
          {line.slice(2)}
        </h2>
      );
    }
    if (line.startsWith("## ")) {
      return (
        <h3 key={key} className="mb-2 mt-5 text-base font-semibold text-neutral-100">
          {line.slice(3)}
        </h3>
      );
    }
    if (line.startsWith("- ")) {
      return (
        <p key={key} className="ml-3 text-sm leading-6 text-neutral-300">
          <span className="text-accent-300">- </span>
          {line.slice(2)}
        </p>
      );
    }
    if (!line.trim()) return <div key={key} className="h-2" />;
    return (
      <p key={key} className="text-sm leading-6 text-neutral-300">
        {line}
      </p>
    );
  });
}
