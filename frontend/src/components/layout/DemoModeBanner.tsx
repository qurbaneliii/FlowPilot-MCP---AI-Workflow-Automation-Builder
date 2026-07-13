import { Info } from "lucide-react";
import type { HealthResponse } from "@/types/api";

export function DemoModeBanner({ health }: { health?: HealthResponse | null }) {
  const services = health?.services;
  const isDemo =
    health?.demo_mode?.active ??
    (services?.mcp?.status === "mock" ||
      services?.openai?.label?.toLowerCase().includes("fake") ||
      services?.database?.status === "memory");
  if (!isDemo) return null;

  return (
    <div className="mx-auto max-w-[1760px] px-4 pt-3 sm:px-6 lg:px-8">
      <div className="demo-mode-banner">
        <Info className="h-4 w-4 shrink-0 text-accent-300" aria-hidden="true" />
        <p>
          <strong>{health?.demo_mode?.label ?? "Demo mode active"}.</strong>{" "}
          {health?.demo_mode?.description ?? "Repository writes are safely mocked, AI responses are deterministic, and run history may reset when the backend restarts."}
        </p>
      </div>
    </div>
  );
}
