import { Play } from "lucide-react";

interface RunButtonProps {
  disabled?: boolean;
  isStarting?: boolean;
  onRun: () => void;
}

export function RunButton({ disabled, isStarting, onRun }: RunButtonProps) {
  return (
    <button
      type="button"
      className="btn-secondary w-full"
      disabled={disabled || isStarting}
      onClick={onRun}
    >
      <Play className="h-4 w-4" aria-hidden="true" />
      {isStarting ? "Starting run..." : "Run workflow"}
    </button>
  );
}
