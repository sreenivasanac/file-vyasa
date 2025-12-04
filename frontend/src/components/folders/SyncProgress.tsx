import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Cpu, Square, Play, AlertTriangle, FileText } from 'lucide-react';
import { Spinner } from '@/components/common/Spinner';
import { Button } from '@/components/common/Button';
import { SyncProgressBar } from '@/components/common/SyncProgressBar';
import { useAppStore } from '@/stores/appStore';
import { useSyncPolling } from '@/hooks/useSyncPolling';
import { api } from '@/api/client';
import { formatDuration } from '@/lib/utils';

/**
 * Compute ETA label from sync progress using moving average calculation.
 */
function computeEtaLabel(syncProgress: {
  total: number;
  processed: number;
  startTime: number | null;
  processingTimes: number[];
}): string | null {
  const { processed, total, startTime, processingTimes } = syncProgress;
  if (!startTime || processed < 3) return null;

  const remaining = total - processed;
  if (remaining <= 0) return null;

  // Use moving average if available, otherwise fall back to overall average
  const avgTimePerFile = processingTimes.length > 0
    ? processingTimes.reduce((a, b) => a + b, 0) / processingTimes.length
    : (Date.now() - startTime) / processed;

  const etaMs = avgTimePerFile * remaining;

  return `~${formatDuration(etaMs)} remaining`;
}

export function SyncProgress() {
  const { currentFolderId, isSyncing, syncProgress, setIsSyncing, folders } =
    useAppStore();
  const queryClient = useQueryClient();
  const [isCancelling, setIsCancelling] = useState(false);
  const [isContinuing, setIsContinuing] = useState(false);

  const currentFolder = folders.find((f) => f.id === currentFolderId);
  const { processingFiles } = useSyncPolling(currentFolderId, isSyncing);

  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: api.config.get,
  });

  const handleCancel = async () => {
    if (!currentFolderId || isCancelling) return;
    setIsCancelling(true);
    try {
      await api.folders.cancel(currentFolderId);
    } catch (err) {
      console.error('Failed to cancel sync:', err);
      setIsCancelling(false);
    }
  };

  const handleContinue = async () => {
    if (!currentFolderId || isContinuing) return;
    setIsContinuing(true);
    try {
      await api.folders.sync(currentFolderId);
      setIsSyncing(true);
      queryClient.invalidateQueries({ queryKey: ['folders'] });
    } catch (err) {
      console.error('Failed to continue sync:', err);
    } finally {
      setIsContinuing(false);
    }
  };

  const isPaused = !isSyncing && currentFolder?.status === 'cancelled';

  if (!isSyncing && !isPaused) return null;

  const displayTotal = isPaused
    ? (currentFolder?.total_files ?? 0)
    : syncProgress.total;
  const displayProcessed = isPaused
    ? (currentFolder?.processed_files ?? 0)
    : syncProgress.processed;
  const displayFailed = isPaused
    ? (currentFolder?.failed_files ?? 0)
    : syncProgress.failed;
  const progress =
    displayTotal > 0 ? Math.round((displayProcessed / displayTotal) * 100) : 0;
  const eta = isSyncing ? computeEtaLabel(syncProgress) : null;

  // Paused state UI
  if (isPaused) {
    return (
      <div className="rounded-lg border border-warning/30 bg-warning/5 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-4 w-4 text-warning" />
            <span className="text-sm font-medium text-text-primary">
              Sync paused
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleContinue}
            disabled={isContinuing}
            className="text-accent hover:bg-accent/10"
          >
            <Play className="mr-1 h-3 w-3" />
            {isContinuing ? 'Resuming...' : 'Continue'}
          </Button>
        </div>

        <SyncProgressBar
          total={displayTotal}
          processed={displayProcessed}
          variant="warning"
        />

        <div className="mt-2 flex justify-between text-xs text-text-muted">
          <span>
            {displayProcessed} / {displayTotal} files processed
          </span>
          {displayFailed > 0 && (
            <span className="text-error">{displayFailed} failed</span>
          )}
          <span>{progress}%</span>
        </div>
      </div>
    );
  }

  // Active syncing UI
  return (
    <div className="rounded-lg border border-border bg-bg-secondary p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Spinner size="sm" className="text-accent" />
          <span className="text-sm font-medium text-text-primary">
            {isCancelling ? 'Stopping sync...' : 'Syncing files...'}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {config && (
            <div className="flex items-center gap-1.5 text-xs text-text-muted">
              <Cpu className="h-3 w-3" />
              <span>
                {config.llm.provider}/{config.llm.model}
              </span>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCancel}
            disabled={isCancelling}
            className="text-error hover:bg-error/10"
          >
            <Square className="mr-1 h-3 w-3" />
            {isCancelling ? 'Stopping...' : 'Stop'}
          </Button>
        </div>
      </div>

      <SyncProgressBar total={displayTotal} processed={displayProcessed} />

      <div className="mt-2 flex justify-between text-xs text-text-muted">
        <span>
          {displayProcessed} / {displayTotal} files processed
        </span>
        {displayFailed > 0 && (
          <span className="text-error">{displayFailed} failed</span>
        )}
        {eta && <span className="text-text-secondary">{eta}</span>}
        <span>{progress}%</span>
      </div>

      {processingFiles.length > 0 && (
        <div className="mt-3 border-t border-border pt-3">
          <div className="mb-2 flex items-center gap-1.5 text-xs text-text-muted">
            <FileText className="h-3 w-3" />
            <span>Currently processing:</span>
          </div>
          <div className="max-h-24 space-y-1 overflow-y-auto">
            {processingFiles.slice(0, 5).map((file) => (
              <div
                key={file.path}
                className="flex items-center gap-2 truncate text-xs text-text-secondary"
              >
                <Spinner size="xs" className="flex-shrink-0 text-accent" />
                <span className="truncate" title={file.path}>
                  {file.filename}
                </span>
              </div>
            ))}
            {processingFiles.length > 5 && (
              <div className="text-xs text-text-muted">
                +{processingFiles.length - 5} more files...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
