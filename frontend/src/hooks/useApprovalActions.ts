"use client";

import { useCallback, useState } from "react";
import { approveApproval, rejectApproval } from "@/lib/api";
import type { Run } from "@/types/run";

type Decision = "approve" | "reject";

interface UseApprovalActionsOptions {
  onSettled?: (run: Run) => void;
}

export function useApprovalActions({ onSettled }: UseApprovalActionsOptions = {}) {
  const [loadingDecision, setLoadingDecision] = useState<Decision | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastDecision, setLastDecision] = useState<string | null>(null);

  const submit = useCallback(
    async (approvalId: string, decision: Decision) => {
      setLoadingDecision(decision);
      setError(null);
      try {
        const response =
          decision === "approve"
            ? await approveApproval(approvalId)
            : await rejectApproval(approvalId);
        setLastDecision(response.decision);
        onSettled?.(response.run);
        return response.run;
      } catch (caught) {
        const message =
          caught instanceof Error
            ? caught.message
            : "Approval action failed in a controlled way.";
        setError(message);
        return null;
      } finally {
        setLoadingDecision(null);
      }
    },
    [onSettled]
  );

  return {
    approve: (approvalId: string) => submit(approvalId, "approve"),
    reject: (approvalId: string) => submit(approvalId, "reject"),
    loadingDecision,
    error,
    lastDecision
  };
}
