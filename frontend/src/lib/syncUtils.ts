import { formatDuration } from './utils';

export interface SyncProgressData {
  total: number;
  processed: number;
  failed: number;
  startTime: number | null;
  lastProcessedTime: number | null;
  processingTimes: number[];
}

// Minimum files needed before showing ETA (avoids startup overhead skewing estimate)
const MIN_FILES_FOR_ETA = 5;
// Number of initial samples to discard (often have startup overhead)
const WARMUP_SAMPLES_TO_DISCARD = 2;
// Samples to use for rolling window after warmup
const ROLLING_WINDOW_SIZE = 15;

/**
 * Compute ETA label from sync progress using improved rolling window calculation.
 * 
 * Improvements over simple average:
 * 1. Waits for MIN_FILES_FOR_ETA files before showing estimate
 * 2. Discards initial WARMUP_SAMPLES_TO_DISCARD samples (startup overhead)
 * 3. Uses rolling window of last ROLLING_WINDOW_SIZE samples for stability
 */
export function computeEtaLabel(syncProgress: SyncProgressData): string | null {
  const { processed, total, startTime, processingTimes } = syncProgress;
  if (!startTime || processed < MIN_FILES_FOR_ETA) return null;

  const remaining = total - processed;
  if (remaining <= 0) return null;

  // Need enough samples after discarding warmup
  if (processingTimes.length <= WARMUP_SAMPLES_TO_DISCARD) return null;

  // Discard initial warmup samples and use rolling window
  const samplesAfterWarmup = processingTimes.slice(WARMUP_SAMPLES_TO_DISCARD);
  const recentSamples = samplesAfterWarmup.slice(-ROLLING_WINDOW_SIZE);
  
  if (recentSamples.length === 0) return null;

  const avgTimePerFile = recentSamples.reduce((a, b) => a + b, 0) / recentSamples.length;
  const etaMs = avgTimePerFile * remaining;
  
  return `~${formatDuration(etaMs)} remaining`;
}

// Keep enough samples: warmup + rolling window
const MAX_PROCESSING_TIMES = WARMUP_SAMPLES_TO_DISCARD + ROLLING_WINDOW_SIZE;

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
