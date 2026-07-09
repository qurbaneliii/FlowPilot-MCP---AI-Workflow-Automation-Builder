import { Activity, GitBranch, Play, ShieldCheck, Terminal } from "lucide-react";

const statuses = [
  { label: "Planner", value: "Ready", tone: "text-accent-300" },
  { label: "Validator", value: "Waiting", tone: "text-neutral-300" },
  { label: "Execution", value: "Idle", tone: "text-neutral-300" }
] as const;

export default function HomePage() {
  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100">
      <section className="border-b border-neutral-800 bg-neutral-900">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-normal text-accent-300">
              FlowPilot MCP
            </p>
            <h1 className="text-xl font-semibold text-neutral-50">
              AI Workflow Automation Builder
            </h1>
          </div>
          <div className="flex items-center gap-2 rounded-md border border-neutral-700 px-3 py-2 text-sm text-neutral-300">
            <Activity className="h-4 w-4 text-accent-300" aria-hidden="true" />
            Phase 0 scaffold
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-4 px-6 py-6 lg:grid-cols-[360px_1fr_340px]">
        <aside className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
          <div className="mb-4 flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-accent-300" aria-hidden="true" />
            <h2 className="text-base font-semibold">Prompt</h2>
          </div>
          <textarea
            className="h-40 w-full resize-none rounded-md border border-neutral-700 bg-neutral-950 p-3 text-sm text-neutral-100 outline-none transition focus-visible:border-accent-400"
            placeholder="Audit qurbaneliii/example-repo and draft guarded improvement issues"
          />
          <button className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-md bg-accent-500 px-3 py-2 text-sm font-medium text-neutral-950 transition hover:bg-accent-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-200">
            <Play className="h-4 w-4" aria-hidden="true" />
            Generate Workflow
          </button>
        </aside>

        <section className="min-h-[520px] rounded-lg border border-neutral-800 bg-neutral-900 p-4">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold">Workflow Canvas</h2>
            <span className="font-mono text-xs text-neutral-400">react-flow-ready</span>
          </div>
          <div className="grid h-[450px] place-items-center rounded-md border border-dashed border-neutral-700 bg-neutral-950">
            <div className="max-w-sm text-center">
              <ShieldCheck className="mx-auto mb-3 h-8 w-8 text-accent-300" aria-hidden="true" />
              <p className="text-sm text-neutral-300">
                Canvas implementation starts in Phase 7 after the backend graph contract is real.
              </p>
            </div>
          </div>
        </section>

        <aside className="space-y-4">
          <section className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
            <h2 className="mb-3 text-base font-semibold">Run Status</h2>
            <div className="space-y-2">
              {statuses.map((status) => (
                <div
                  key={status.label}
                  className="flex items-center justify-between rounded-md border border-neutral-800 bg-neutral-950 px-3 py-2"
                >
                  <span className="text-sm text-neutral-300">{status.label}</span>
                  <span className={`font-mono text-xs ${status.tone}`}>{status.value}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
            <div className="mb-3 flex items-center gap-2">
              <Terminal className="h-4 w-4 text-accent-300" aria-hidden="true" />
              <h2 className="text-base font-semibold">Logs</h2>
            </div>
            <pre className="min-h-40 overflow-auto rounded-md bg-neutral-950 p-3 font-mono text-xs leading-5 text-neutral-300">
{`[system] backend: /api/v1/health
[system] frontend: app shell
[system] phase: scaffolding`}
            </pre>
          </section>
        </aside>
      </section>
    </main>
  );
}
