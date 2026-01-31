import { getReport } from "./api";
import type { Report } from "@verifai/shared/src/types";

export interface PollOptions {
  jobId: string;
  onUpdate: (report: Report) => void;
  onError: (error: Error) => void;
  initialIntervalMs?: number;
  backoffIntervalMs?: number;
  backoffAfterMs?: number;
  timeoutMs?: number;
}

export function pollReport(options: PollOptions): () => void {
  const {
    jobId,
    onUpdate,
    onError,
    initialIntervalMs = 2000,
    backoffIntervalMs = 5000,
    backoffAfterMs = 30000,
    timeoutMs = 300000,
  } = options;

  let timer: ReturnType<typeof setTimeout> | null = null;
  let stopped = false;
  const startTime = Date.now();

  async function tick() {
    if (stopped) return;

    try {
      const report = await getReport(jobId);
      if (stopped) return;

      onUpdate(report);

      if (report.status === "done" || report.status === "failed") {
        return; // Terminal state, stop polling
      }

      // Check timeout
      const elapsed = Date.now() - startTime;
      if (elapsed >= timeoutMs) {
        onError(new Error("Polling timed out. The analysis is taking longer than expected."));
        return;
      }

      // Schedule next poll with backoff
      const interval = elapsed >= backoffAfterMs ? backoffIntervalMs : initialIntervalMs;
      timer = setTimeout(tick, interval);
    } catch (err) {
      if (stopped) return;
      onError(err instanceof Error ? err : new Error("Polling failed"));
    }
  }

  // Start first poll immediately
  tick();

  // Return cancel function
  return () => {
    stopped = true;
    if (timer) clearTimeout(timer);
  };
}
