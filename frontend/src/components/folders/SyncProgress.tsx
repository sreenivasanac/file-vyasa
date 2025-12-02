import { useEffect, useState, useCallback, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Cpu, Square, Play, AlertTriangle, FileText } from 'lucide-react';
import { Spinner } from '@/components/common/Spinner';
import { Button } from '@/components/common/Button';
import { useAppStore } from '@/stores/appStore';
import { api } from '@/api/client';

interface ProcessingFile {
  path: string;
  filename: string;
}

export function SyncProgress() {
  const {
    currentFolderId,
    isSyncing,
    syncProgress,
    setSyncProgress,
    setIsSyncing,
    clearSyncTiming,
    folders,
  } = useAppStore();

  const queryClient = useQueryClient();
  const [isCancelling, setIsCancelling] = useState(false);
  const [isContinuing, setIsContinuing] = useState(false);
  const [eta, setEta] = useState<string | null>(null);
  const [processingFiles, setProcessingFiles] = useState<ProcessingFile[]>([]);
  const clearSyncTimingRef = useRef(clearSyncTiming);
  
  const currentFolder = folders.find((f) => f.id === currentFolderId);
  
  // Keep ref updated
  useEffect(() => {
    clearSyncTimingRef.current = clearSyncTiming;
  }, [clearSyncTiming]);

  const formatETA = useCallback((ms: number): string => {
    if (ms < 60000) return `${Math.ceil(ms / 1000)}s`;
    if (ms < 3600000) {
      const mins = Math.floor(ms / 60000);
      const secs = Math.ceil((ms % 60000) / 1000);
      return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
    }
    const hours = Math.floor(ms / 3600000);
    const mins = Math.ceil((ms % 3600000) / 60000);
    return `${hours}h ${mins}m`;
  }, []);

  // Fetch current LLM config to show model being used
  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: api.config.get,
  });

  useEffect(() => {
    if (!currentFolderId || !isSyncing) {
      setProcessingFiles([]);
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        // Fetch folder status and processing files in parallel
        const [folder, processingData] = await Promise.all([
          api.folders.get(currentFolderId),
          api.folders.getProcessing(currentFolderId),
        ]);

        setSyncProgress({
          total: folder.total_files,
          processed: folder.processed_files,
          failed: folder.failed_files,
        });

        setProcessingFiles(processingData.processing_files);

        if (folder.status === 'idle' || folder.status === 'error' || folder.status === 'cancelled') {
          setIsSyncing(false);
          setIsCancelling(false);
          setProcessingFiles([]);
          clearSyncTimingRef.current();
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
  
  // Calculate ETA in an effect to avoid impure Date.now() during render
  const calculateEta = useCallback(() => {
    const { processed, total, startTime, processingTimes } = syncProgress;
    if (!startTime || processed < 3) return null;
    
    const remaining = total - processed;
    if (remaining <= 0) return null;
    
    const avgTimePerFile = processingTimes.length > 0
      ? processingTimes.reduce((a, b) => a + b, 0) / processingTimes.length
      : (Date.now() - startTime) / processed;
    
    const etaMs = avgTimePerFile * remaining;
    return `~${formatETA(etaMs)} remaining`;
  }, [syncProgress, formatETA]);
  
  useEffect(() => {
    if (!isSyncing) {
      // Use a timeout to avoid synchronous setState in effect body
      const timeout = setTimeout(() => setEta(null), 0);
      return () => clearTimeout(timeout);
    }
    
    // Update ETA every second via interval callback
    const interval = setInterval(() => {
      setEta(calculateEta());
    }, 100); // Start quickly, then update every 100ms for responsiveness
    
    return () => clearInterval(interval);
  }, [isSyncing, calculateEta]);

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

  // Show paused state when folder is cancelled
  const isPaused = !isSyncing && currentFolder?.status === 'cancelled';
  
  if (!isSyncing && !isPaused) return null;

  // Use folder data for paused state, syncProgress for active sync
  const displayTotal = isPaused ? (currentFolder?.total_files ?? 0) : syncProgress.total;
  const displayProcessed = isPaused ? (currentFolder?.processed_files ?? 0) : syncProgress.processed;
  const displayFailed = isPaused ? (currentFolder?.failed_files ?? 0) : syncProgress.failed;
  
  const progress =
    displayTotal > 0
      ? Math.round((displayProcessed / displayTotal) * 100)
      : 0;

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

        <div className="mb-2 h-2 overflow-hidden rounded-full bg-bg-tertiary">
          <div
            className="h-full bg-warning transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="flex justify-between text-xs text-text-muted">
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
          {displayProcessed} / {displayTotal} files processed
        </span>
        {displayFailed > 0 && (
          <span className="text-error">{displayFailed} failed</span>
        )}
        {eta && <span className="text-text-secondary">{eta}</span>}
        <span>{progress}%</span>
      </div>

      {/* Currently processing files */}
      {processingFiles.length > 0 && (
        <div className="mt-3 border-t border-border pt-3">
          <div className="mb-2 flex items-center gap-1.5 text-xs text-text-muted">
            <FileText className="h-3 w-3" />
            <span>Currently processing:</span>
          </div>
          <div className="max-h-24 overflow-y-auto space-y-1">
            {processingFiles.slice(0, 5).map((file) => (
              <div
                key={file.path}
                className="flex items-center gap-2 text-xs text-text-secondary truncate"
              >
                <Spinner size="xs" className="text-accent flex-shrink-0" />
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
