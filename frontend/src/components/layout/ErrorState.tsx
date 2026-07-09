import { AlertCircle } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message: string;
}

export function ErrorState({ title = "Action failed", message }: ErrorStateProps) {
  return (
    <div
      className="rounded-md border border-status-danger/45 bg-status-danger/10 p-3 text-sm text-neutral-100"
      role="alert"
    >
      <div className="flex gap-2">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-status-danger" />
        <div>
          <p className="font-medium text-status-danger">{title}</p>
          <p className="mt-1 leading-6 text-neutral-300">{message}</p>
        </div>
      </div>
    </div>
  );
}
