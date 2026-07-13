import { Activity, Database, Network, Sparkles } from "lucide-react";
import { StatusPill } from "./StatusPill";
import type { HealthResponse } from "@/types/api";

interface HeaderProps {
  health?: HealthResponse | null;
  healthError?: string | null;
  mode?: string | null;
}

export function Header({ health, healthError, mode }: HeaderProps) {
  const backendStatus = healthError ? "failed" : health ? "completed" : "running";
  const databaseService = health?.services?.database;
  const mcpService = health?.services?.mcp;
  const backendService = health?.services?.backend;
  const openaiService = health?.services?.openai;
  const databaseLabel =
    databaseService?.label ??
    (health?.dependencies.database === "ok"
      ? "DB connected"
      : health?.dependencies.database === "error"
        ? "Memory mode"
        : health?.dependencies.database === "not_configured"
          ? "DB not configured"
          : "DB checking");
  const modeLabel =
    mcpService?.status === "real"
      ? "Real GitHub"
      : mcpService?.status === "mock"
        ? "Safe GitHub demo"
        : health?.ui?.primary_mode_label ??
    mcpService?.label ??
    (mode === "real"
      ? "Real MCP"
      : mode === "mock"
        ? "Mock MCP"
        : health?.dependencies.openai === "not_configured"
          ? "OpenAI not configured"
          : "Mode pending");
  const databaseWarningClass =
    databaseService?.blocking === true
      ? "border-status-danger/25 bg-status-danger/5 text-neutral-300"
      : "border-status-warning/25 bg-status-warning/5 text-neutral-300";
  const databaseIconClass =
    databaseService?.blocking === true ? "text-status-danger" : "text-status-warning";
  const githubExplanation =
    mcpService?.status === "real"
      ? "Live GitHub repository access is enabled."
      : mcpService?.status === "mock"
        ? "Safe local mode: repository reads and writes use deterministic mock data."
        : "Checking GitHub access mode.";
  const agentLabel =
    openaiService?.status === "real"
      ? "Real OpenAI"
      : openaiService
        ? "Local AI demo"
        : "AI checking";
  const agentExplanation =
    openaiService?.status === "real"
      ? "Live OpenAI model analysis is enabled."
      : openaiService
        ? "Deterministic local AI responses keep the demo repeatable and secrets-free."
        : "Checking AI analysis mode.";
  const storageExplanation =
    databaseService?.status === "memory"
      ? "Run history resets when the backend restarts."
      : databaseService?.status === "ok"
        ? "Run history is stored persistently in Postgres."
        : "Checking storage configuration.";
  return (
    <header className="sticky top-0 z-20 border-b border-neutral-800/80 bg-neutral-950/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1760px] flex-col gap-3 px-4 py-3 sm:px-6 lg:h-[76px] lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-md border border-accent-400/30 bg-accent-400/10 shadow-soft">
            <Network className="h-5 w-5 text-accent-300" aria-hidden="true" />
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-normal text-accent-300">
              FlowPilot MCP
            </p>
            <h1 className="text-lg font-semibold text-neutral-50">
              AI Workflow Automation Builder
            </h1>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusPill status={backendStatus} label={healthError ? "Backend offline" : backendService?.label ?? "Backend connected"} />
          <span className="status-chip" title={githubExplanation}>
            <Sparkles className="h-3.5 w-3.5 text-accent-300" aria-hidden="true" />
            {modeLabel}
          </span>
          <span className="status-chip" title={agentExplanation}>
            <Sparkles className="h-3.5 w-3.5 text-violet-300" aria-hidden="true" />
            {agentLabel}
          </span>
          <span className={`status-chip ${databaseWarningClass}`} title={storageExplanation}>
            <Database className={`h-3.5 w-3.5 ${databaseIconClass}`} aria-hidden="true" />
            {databaseLabel}
          </span>
          <span className="status-chip text-neutral-500">
            <Activity className="h-3.5 w-3.5 text-neutral-400" aria-hidden="true" />
            v{health?.version ?? "local"}
          </span>
        </div>
      </div>
    </header>
  );
}
