import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  label: string;
}

export function LoadingState({ label }: LoadingStateProps) {
  return (
    <div className="flex min-h-32 items-center justify-center rounded-md border border-neutral-800 bg-neutral-950/55 text-sm text-neutral-300">
      <Loader2 className="mr-2 h-4 w-4 animate-spin text-status-running" aria-hidden="true" />
      {label}
    </div>
  );
}
