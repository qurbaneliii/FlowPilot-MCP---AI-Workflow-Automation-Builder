import type { ReactNode } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import type { HealthResponse } from "@/types/api";

interface AppShellProps {
  children: ReactNode;
  health?: HealthResponse | null;
  healthError?: string | null;
  mode?: string | null;
}

export function AppShell({ children, health, healthError, mode }: AppShellProps) {
  return (
    <div className="min-h-screen bg-page text-neutral-100">
      <Header health={health} healthError={healthError} mode={mode} />
      <div className="mx-auto grid max-w-[1760px] xl:grid-cols-[76px_1fr]">
        <Sidebar />
        <main className="min-w-0 px-4 py-5 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
