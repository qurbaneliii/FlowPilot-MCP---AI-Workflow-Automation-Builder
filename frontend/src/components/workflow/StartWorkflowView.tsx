"use client";

import { CheckCircle2 } from "lucide-react";
import { SectionCard } from "@/components/layout/SectionCard";
import { PromptInputPanel } from "./PromptInputPanel";
import { GuidedStepper } from "./GuidedStepper";
import { NextActionCard } from "./NextActionCard";

interface StartWorkflowViewProps {
  prompt: string;
  repoUrl: string;
  validationErrors: string[];
  isGenerating: boolean;
  error?: string | null;
  onPromptChange: (value: string) => void;
  onRepoUrlChange: (value: string) => void;
  onGenerate: () => void;
}

const outcomes = [
  "Build an executable workflow graph",
  "Read repository files and project structure",
  "Analyze README quality and readiness",
  "Draft actionable GitHub issues",
  "Ask before any issue creation",
  "Generate reports and a LinkedIn draft"
];

export function StartWorkflowView(props: StartWorkflowViewProps) {
  return (
    <div id="builder" className="space-y-5">
      <GuidedStepper />
      <NextActionCard />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_430px]">
      <section className="hero-panel">
        <p className="kicker">AI workflow automation control plane</p>
        <h2 className="mt-3 max-w-4xl text-3xl font-semibold tracking-normal text-neutral-50 sm:text-4xl">
          Audit a GitHub repository with a guided, approval-safe AI workflow.
        </h2>
        <p className="mt-4 max-w-2xl text-base leading-7 text-neutral-300">
          Tell FlowPilot what to review and which public repository to inspect. It builds the workflow, explains every step, and pauses before creating GitHub issues.
        </p>
        <div className="mt-7">
          <p className="mb-3 text-sm font-semibold text-neutral-100">What FlowPilot will do</p>
          <div className="grid gap-x-5 gap-y-3 sm:grid-cols-2">
          {outcomes.map((outcome) => {
            return (
              <div key={outcome} className="flex items-start gap-2 text-sm leading-6 text-neutral-300">
                <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-status-success" aria-hidden="true" />
                <span>{outcome}</span>
              </div>
            );
          })}
          </div>
        </div>
      </section>

      <SectionCard title="Build Workflow" eyebrow="Prompt">
        <PromptInputPanel {...props} />
      </SectionCard>
      </div>
    </div>
  );
}
