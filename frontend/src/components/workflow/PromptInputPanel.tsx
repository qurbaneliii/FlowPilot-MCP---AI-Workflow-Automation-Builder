"use client";

import { Github, Wand2 } from "lucide-react";
import { EXAMPLE_PROMPTS } from "@/lib/constants";
import { ErrorState } from "@/components/layout/ErrorState";

interface PromptInputPanelProps {
  prompt: string;
  repoUrl: string;
  validationErrors: string[];
  isGenerating: boolean;
  error?: string | null;
  onPromptChange: (value: string) => void;
  onRepoUrlChange: (value: string) => void;
  onGenerate: () => void;
}

export function PromptInputPanel({
  prompt,
  repoUrl,
  validationErrors,
  isGenerating,
  error,
  onPromptChange,
  onRepoUrlChange,
  onGenerate
}: PromptInputPanelProps) {
  const useDemoRepo = () => {
    onRepoUrlChange("https://github.com/openai/openai-python");
    onPromptChange("Audit this GitHub repository and draft guarded improvement issues.");
  };
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="prompt" className="form-label">
          Automation request
        </label>
        <textarea
          id="prompt"
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          className="form-textarea min-h-32"
          placeholder="Audit this GitHub repository and draft guarded improvement issues."
        />
      </div>
      <div>
        <label htmlFor="repo-url" className="form-label">
          GitHub repository URL
        </label>
        <input
          id="repo-url"
          value={repoUrl}
          onChange={(event) => onRepoUrlChange(event.target.value)}
          className="form-input"
          placeholder="https://github.com/owner/repo"
        />
        <button type="button" className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-accent-300 hover:text-accent-200" onClick={useDemoRepo}>
          <Github className="h-3.5 w-3.5" aria-hidden="true" />
          Use demo repo: openai/openai-python
        </button>
      </div>
      <p className="text-xs leading-5 text-neutral-500">FlowPilot will not run or create anything until you choose the next action.</p>
      <div className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map((example) => (
          <button
            key={example}
            type="button"
            className="rounded-md border border-neutral-800 bg-neutral-950 px-2.5 py-1.5 text-left text-xs text-neutral-300 transition hover:border-accent-500/60 hover:text-neutral-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent-300"
            onClick={() => onPromptChange(example)}
          >
            {example}
          </button>
        ))}
      </div>
      {validationErrors.length > 0 && repoUrl.trim().length > 0 && (
        <p className="text-xs leading-5 text-status-warning">
          {validationErrors[0]}
        </p>
      )}
      {error && <ErrorState title="Workflow generation failed" message={error} />}
      <button
        type="button"
        className="btn-primary w-full"
        disabled={isGenerating || validationErrors.length > 0}
        onClick={onGenerate}
      >
        <Wand2 className="h-4 w-4" aria-hidden="true" />
        {isGenerating ? "Building your workflow..." : "Generate workflow"}
      </button>
    </div>
  );
}
