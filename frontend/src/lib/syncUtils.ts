import { formatDuration } from './utils';

export interface SyncProgressData {
  total: number;
  processed: number;
  failed: number;
  startTime: number | null;
  lastProcessedTime: number | null;
  processingTimes: number[];
}

/**
 * Compute ETA label from sync progress using moving average calculation.
 */
export function computeEtaLabel(syncProgress: SyncProgressData): string | null {
  const { processed, total, startTime, processingTimes } = syncProgress;
  if (!startTime || processed < 3) return null;

  const remaining = total - processed;
  if (remaining <= 0) return null;

  const avgTimePerFile =
    processingTimes.length > 0
      ? processingTimes.reduce((a, b) => a + b, 0) / processingTimes.length
      : (Date.now() - startTime) / processed;

  const etaMs = avgTimePerFile * remaining;
  return `~${formatDuration(etaMs)} remaining`;
}

const MAX_PROCESSING_TIMES = 20;

/**
 * Calculate updated processing times array based on newly processed files.
 * Uses a moving average of the last 20 file processing times.
 */
export function calculateProcessingTimes(
  prevTimes: number[],
  prevLastProcessedTime: number | null,
  now: number,
  newlyProcessed: number
): { processingTimes: number[]; lastProcessedTime: number } {
  let processingTimes = [...prevTimes];
  let lastProcessedTime = prevLastProcessedTime ?? now;

  if (newlyProcessed > 0 && prevLastProcessedTime !== null) {
    const elapsed = now - prevLastProcessedTime;
    const avgTimePerNewFile = elapsed / newlyProcessed;
    for (let i = 0; i < newlyProcessed; i++) {
      processingTimes.push(avgTimePerNewFile);
    }
    if (processingTimes.length > MAX_PROCESSING_TIMES) {
      processingTimes = processingTimes.slice(-MAX_PROCESSING_TIMES);
    }
    lastProcessedTime = now;
  } else if (newlyProcessed > 0) {
    lastProcessedTime = now;
  }

  return { processingTimes, lastProcessedTime };
}

/**
 * Create updated sync progress state from incoming progress update.
 */
export function updateSyncProgress(
  prev: SyncProgressData,
  update: { total: number; processed: number; failed: number }
): SyncProgressData {
  const now = Date.now();
  const startTime = prev.startTime ?? now;
  const newlyProcessed = update.processed - prev.processed;

  const { processingTimes, lastProcessedTime } = calculateProcessingTimes(
    prev.processingTimes,
    prev.lastProcessedTime,
    now,
    newlyProcessed
  );

  return {
    ...update,
    startTime,
    lastProcessedTime,
    processingTimes,
  };
}

/**
 * Initial sync progress state.
 */
export const INITIAL_SYNC_PROGRESS: SyncProgressData = {
  total: 0,
  processed: 0,
  failed: 0,
  startTime: null,
  lastProcessedTime: null,
  processingTimes: [],
};
