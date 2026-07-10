import { StatusPill } from "@/components/layout/StatusPill";

export function RunStatusBadge({ status }: { status?: string | null }) {
  return <StatusPill status={status ?? "pending"} />;
}
