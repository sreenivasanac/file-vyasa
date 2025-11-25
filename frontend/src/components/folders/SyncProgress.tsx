import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Cpu, Square } from 'lucide-react';
import { Spinner } from '@/components/common/Spinner';
import { Button } from '@/components/common/Button';
import { useAppStore } from '@/stores/appStore';
import { api } from '@/api/client';

export function SyncProgress() {
  const {
    currentFolderId,
    isSyncing,
    syncProgress,
    setSyncProgress,
    setIsSyncing,
  } = useAppStore();

  const queryClient = useQueryClient();
  const [isCancelling, setIsCancelling] = useState(false);

  // Fetch current LLM config to show model being used
  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: api.config.get,
  });

  useEffect(() => {
    if (!currentFolderId || !isSyncing) return;

    const pollInterval = setInterval(async () => {
      try {
        const folder = await api.folders.get(currentFolderId);
        setSyncProgress({
          total: folder.total_files,
          processed: folder.processed_files,
          failed: folder.failed_files,
        });

        if (folder.status === 'idle' || folder.status === 'error' || folder.status === 'cancelled') {
          setIsSyncing(false);
          setIsCancelling(false);
          // Refresh folders list and files
          queryClient.invalidateQueries({ queryKey: ['folders'] });
          queryClient.invalidateQueries({ queryKey: ['files'] });
        }
      } catch (err) {
        console.error('Failed to poll folder status:', err);
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [currentFolderId, isSyncing, setSyncProgress, setIsSyncing, queryClient]);

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

  if (!isSyncing) return null;

  const progress =
    syncProgress.total > 0
      ? Math.round((syncProgress.processed / syncProgress.total) * 100)
      : 0;

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
              <span>{config.llm.provider}/{config.llm.model}</span>
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

      <div className="mb-2 h-2 overflow-hidden rounded-full bg-bg-tertiary">
        <div
          className="h-full bg-accent transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex justify-between text-xs text-text-muted">
        <span>
          {syncProgress.processed} / {syncProgress.total} files processed
        </span>
        {syncProgress.failed > 0 && (
          <span className="text-error">{syncProgress.failed} failed</span>
        )}
        <span>{progress}%</span>
      </div>
    </div>
  );
}
