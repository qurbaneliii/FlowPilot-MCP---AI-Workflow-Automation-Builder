import type { LucideIcon } from "lucide-react";
import { Circle } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
}

export function EmptyState({ title, description, icon: Icon = Circle }: EmptyStateProps) {
  return (
    <div className="grid min-h-40 place-items-center rounded-md border border-dashed border-neutral-800 bg-neutral-950/55 p-6 text-center">
      <div className="max-w-sm">
        <Icon className="mx-auto mb-3 h-8 w-8 text-neutral-500" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-neutral-100">{title}</h3>
        <p className="mt-1 text-sm leading-6 text-neutral-400">{description}</p>
      </div>
    </div>
  );
}
