import { Check, Circle, X } from "lucide-react";
import type { RunStatus } from "@/types/run";
import type { GuidedSteps } from "@/types/ui";

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
  guidedSteps?: GuidedSteps | null;
}

export function GuidedStepper({ hasWorkflow = false, runStatus, guidedSteps }: GuidedStepperProps) {
  const activeIndex = getActiveIndex(hasWorkflow, runStatus);
  const failed = runStatus === "failed";
  const renderedSteps = guidedSteps?.steps?.length
    ? guidedSteps.steps
    : steps.map((label, index) => ({
        id: label,
        label,
        description: label,
        status:
          failed && index === activeIndex
            ? "failed"
            : index < activeIndex || (runStatus === "completed" && index <= activeIndex)
              ? "completed"
              : index === activeIndex
                ? "active"
                : "pending"
      }));

  return (
    <nav className="guided-stepper" aria-label="Workflow progress">
      {renderedSteps.map((step, index) => {
        const completed = step.status === "completed";
        const active = step.status === "active";
        const error = step.status === "failed";
        return (
          <div
            key={step.id}
            className={`guided-step ${completed ? "guided-step-completed" : ""} ${active ? "guided-step-active" : ""} ${error ? "guided-step-error" : ""}`}
            aria-current={active ? "step" : undefined}
            title={step.description}
          >
            <span className="guided-step-marker">
              {error ? <X aria-hidden="true" /> : completed ? <Check aria-hidden="true" /> : <Circle aria-hidden="true" />}
            </span>
            <span>
              <span className="guided-step-number">Step {index + 1}</span>
              <span className="guided-step-label">{step.label}</span>
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
