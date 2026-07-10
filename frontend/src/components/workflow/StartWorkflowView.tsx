"use client";

import { CheckCircle2, FileText, GitBranch, ShieldCheck } from "lucide-react";
import { SectionCard } from "@/components/layout/SectionCard";
import { PromptInputPanel } from "./PromptInputPanel";

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

const steps = [
  { label: "Plan workflow graph", icon: GitBranch },
  { label: "Audit repository", icon: CheckCircle2 },
  { label: "Request approval before writes", icon: ShieldCheck },
  { label: "Produce reports and draft copy", icon: FileText }
];

export function StartWorkflowView(props: StartWorkflowViewProps) {
  return (
    <div id="builder" className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_430px]">
      <section className="hero-panel">
        <p className="kicker">AI workflow automation control plane</p>
        <h2 className="mt-3 max-w-4xl text-3xl font-semibold tracking-normal text-neutral-50 sm:text-4xl">
          Turn a natural language automation request into an executable workflow graph.
        </h2>
        <p className="mt-4 max-w-2xl text-base leading-7 text-neutral-300">
          FlowPilot MCP plans repository audits, runs deterministic or real
          MCP-backed nodes, pauses before external writes, and renders
          interview-ready artifacts.
        </p>
        <div className="mt-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div key={step.label} className="quiet-metric">
                <Icon className="h-4 w-4 text-accent-300" aria-hidden="true" />
                <span>{step.label}</span>
              </div>
            );
          })}
        </div>
      </section>

      <SectionCard title="Build Workflow" eyebrow="Prompt">
        <PromptInputPanel {...props} />
      </SectionCard>
    </div>
  );
}
