"use client";

import { useCallback, useMemo, useState } from "react";
import { FlowPilotApiError, generateWorkflow } from "@/lib/api";
import type { GeneratedWorkflow } from "@/types/workflow";

const GITHUB_REPO_RE =
  /^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?(?:\.git)?$/;

export function useWorkflow() {
  const [prompt, setPrompt] = useState(
    "Audit this GitHub repository and draft guarded improvement issues."
  );
  const [repoUrl, setRepoUrl] = useState("");
  const [workflow, setWorkflow] = useState<GeneratedWorkflow | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validationErrors = useMemo(() => {
    const errors: string[] = [];
    if (!prompt.trim()) errors.push("Describe the automation request.");
    if (!repoUrl.trim()) {
      errors.push("Provide a GitHub repository URL.");
    } else if (!GITHUB_REPO_RE.test(repoUrl.trim())) {
      errors.push("Repository URL must look like https://github.com/owner/repo.");
    }
    return errors;
  }, [prompt, repoUrl]);

  const generate = useCallback(async () => {
    setError(null);
    if (validationErrors.length) {
      setError(validationErrors[0]);
      return null;
    }
    setIsGenerating(true);
    try {
      const response = await generateWorkflow({
        prompt: prompt.trim(),
        repo_url: repoUrl.trim()
      });
      setWorkflow(response);
      return response;
    } catch (caught) {
      const message =
        caught instanceof FlowPilotApiError
          ? friendlyApiError(caught)
          : caught instanceof Error
          ? friendlyGenerationError(caught.message)
          : "Workflow generation failed in a controlled way.";
      setError(message);
      return null;
    } finally {
      setIsGenerating(false);
    }
  }, [prompt, repoUrl, validationErrors]);

  return {
    prompt,
    setPrompt,
    repoUrl,
    setRepoUrl,
    workflow,
    setWorkflow,
    validationErrors,
    isGenerating,
    error,
    generate
  };
}

function friendlyApiError(error: FlowPilotApiError): string {
  const example = error.details?.example;
  if (typeof example === "string") {
    return `${error.message} For example: ${example}`;
  }
  return friendlyGenerationError(error.message);
}

function friendlyGenerationError(message: string): string {
  if (message.toLowerCase().includes("repo") || message.toLowerCase().includes("github")) {
    return "Enter a valid public GitHub repository URL, for example https://github.com/openai/openai-python.";
  }
  return `FlowPilot could not generate this workflow. ${message}`;
}
