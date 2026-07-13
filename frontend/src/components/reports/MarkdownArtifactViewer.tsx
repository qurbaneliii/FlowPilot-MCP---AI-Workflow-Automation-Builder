import { FileText } from "lucide-react";
import { CopyButton } from "@/components/layout/CopyButton";
import { formatTimestamp, titleCase } from "@/lib/formatters";
import type { Artifact } from "@/types/artifact";

interface MarkdownArtifactViewerProps {
  artifact?: Artifact | null;
  fallbackTitle: string;
}

export function MarkdownArtifactViewer({
  artifact,
  fallbackTitle
}: MarkdownArtifactViewerProps) {
  if (!artifact) {
    return (
      <div className="rounded-md border border-dashed border-neutral-800 bg-neutral-950/55 p-6 text-sm text-neutral-400">
        {fallbackTitle} will appear here after the workflow completes.
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
              {titleCase(artifact.artifact_type)} · Generated {formatTimestamp(artifact.created_at)} · {artifact.mode ?? "mode pending"} mode
            </p>
          </div>
        </div>
        <CopyButton value={artifact.content} label="Copy report" />
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
