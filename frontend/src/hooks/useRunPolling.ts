"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getRun, runWorkflow } from "@/lib/api";
import { ACTIVE_RUN_STATUSES, TERMINAL_RUN_STATUSES } from "@/lib/constants";
import type { Run } from "@/types/run";

interface UseRunPollingOptions {
  workflowId?: string;
  initialRunId?: string;
  intervalMs?: number;
}

export function useRunPolling({
  workflowId,
  initialRunId,
  intervalMs = 1600
}: UseRunPollingOptions = {}) {
  const [runId, setRunId] = useState<string | null>(initialRunId ?? null);
  const [run, setRun] = useState<Run | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(
    async (overrideRunId?: string) => {
      const id = overrideRunId ?? runId;
      if (!id) return null;
      setIsFetching(true);
      try {
        const response = await getRun(id);
        setRun(response);
        setError(null);
        return response;
      } catch (caught) {
        const message =
          caught instanceof Error
            ? caught.message
            : "Run polling failed in a controlled way.";
        setError(message);
        return null;
      } finally {
        setIsFetching(false);
      }
    },
    [runId]
  );

  const startRun = useCallback(
    async (workflowOverride?: string) => {
      const id = workflowOverride ?? workflowId;
      if (!id) {
        setError("Generate a workflow before starting a run.");
        return null;
      }
      setIsStarting(true);
      setError(null);
      try {
        const response = await runWorkflow(id);
        setRunId(response.run_id);
        return await refresh(response.run_id);
      } catch (caught) {
        const message =
          caught instanceof Error ? caught.message : "Run start failed.";
        setError(message);
        return null;
      } finally {
        setIsStarting(false);
      }
    },
    [refresh, workflowId]
  );

  useEffect(() => {
    if (!initialRunId) return;
    const timeout = window.setTimeout(() => {
      void refresh(initialRunId);
    }, 0);
    return () => window.clearTimeout(timeout);
  }, [initialRunId, refresh]);

  useEffect(() => {
    if (!runId || !run || TERMINAL_RUN_STATUSES.has(run.status)) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }
    if (!ACTIVE_RUN_STATUSES.has(run.status) || intervalRef.current) return;
    intervalRef.current = setInterval(() => {
      void refresh(runId);
    }, intervalMs);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [intervalMs, refresh, run, runId]);

  const setRunFromAction = useCallback((nextRun: Run) => {
    setRun(nextRun);
    setRunId(nextRun.run_id);
  }, []);

  return {
    runId,
    run,
    isStarting,
    isFetching,
    isPolling: Boolean(run && ACTIVE_RUN_STATUSES.has(run.status)),
    error,
    startRun,
    refresh,
    setRunFromAction
  };
}
