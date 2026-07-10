import { getStatusMeta } from "@/lib/constants";

interface StatusPillProps {
  status?: string | null;
  label?: string;
  compact?: boolean;
}

export function StatusPill({ status, label, compact = false }: StatusPillProps) {
  const meta = getStatusMeta(status);
  const Icon = meta.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 font-mono text-[11px] font-medium uppercase leading-none tracking-normal ${meta.className}`}
      aria-label={`Status: ${label ?? meta.label}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${meta.dotClassName}`} />
      {!compact && <Icon className="h-3 w-3" aria-hidden="true" />}
      {label ?? meta.label}
    </span>
  );
}
