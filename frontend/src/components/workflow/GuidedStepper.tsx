import { Check, Circle, X } from "lucide-react";
import type { RunStatus } from "@/types/run";

const steps = [
  "Define Task",
  "Generate Workflow",
  "Run Automation",
  "Review Approval",
  "View Outputs"
] as const;

interface GuidedStepperProps {
  hasWorkflow?: boolean;
  runStatus?: RunStatus | null;
}

export function GuidedStepper({ hasWorkflow = false, runStatus }: GuidedStepperProps) {
  const activeIndex = getActiveIndex(hasWorkflow, runStatus);
  const failed = runStatus === "failed";

  return (
    <nav className="guided-stepper" aria-label="Workflow progress">
      {steps.map((label, index) => {
        const completed = index < activeIndex || (runStatus === "completed" && index <= activeIndex);
        const active = index === activeIndex;
        const error = failed && active;
        return (
          <div
            key={label}
            className={`guided-step ${completed ? "guided-step-completed" : ""} ${active ? "guided-step-active" : ""} ${error ? "guided-step-error" : ""}`}
            aria-current={active ? "step" : undefined}
          >
            <span className="guided-step-marker">
              {error ? <X aria-hidden="true" /> : completed ? <Check aria-hidden="true" /> : <Circle aria-hidden="true" />}
            </span>
            <span>
              <span className="guided-step-number">Step {index + 1}</span>
              <span className="guided-step-label">{label}</span>
            </span>
          </div>
        );
      })}
    </nav>
  );
}

function getActiveIndex(hasWorkflow: boolean, status?: RunStatus | null) {
  if (!hasWorkflow) return 0;
  if (!status) return 2;
  if (status === "waiting_for_approval") return 3;
  if (status === "completed") return 4;
  return 2;
}
