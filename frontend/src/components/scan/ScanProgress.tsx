import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Cpu, Square } from 'lucide-react';
import { Spinner } from '@/components/common/Spinner';
import { Button } from '@/components/common/Button';
import { useAppStore } from '@/stores/appStore';
import { api } from '@/api/client';

export function ScanProgress() {
  const {
    currentScanId,
    isScanning,
    scanProgress,
    setScanProgress,
    setIsScanning,
  } = useAppStore();

  const [isCancelling, setIsCancelling] = useState(false);

  // Fetch current LLM config to show model being used
  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: api.config.get,
  });

  useEffect(() => {
    if (!currentScanId || !isScanning) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await api.scan.status(currentScanId, false);
        setScanProgress({
          total: status.total_files,
          processed: status.processed_files,
          failed: status.failed_files,
        });

        if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
          setIsScanning(false);
          setIsCancelling(false);
        }
      } catch (err) {
        console.error('Failed to poll scan status:', err);
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [currentScanId, isScanning, setScanProgress, setIsScanning]);

  const handleCancel = async () => {
    if (!currentScanId || isCancelling) return;
    setIsCancelling(true);
    try {
      await api.scan.cancel(currentScanId);
    } catch (err) {
      console.error('Failed to cancel scan:', err);
      setIsCancelling(false);
    }
  };

  if (!isScanning) return null;

  const progress =
    scanProgress.total > 0
      ? Math.round((scanProgress.processed / scanProgress.total) * 100)
      : 0;

  return (
    <div className="rounded-lg border border-border bg-bg-secondary p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Spinner size="sm" className="text-accent" />
          <span className="text-sm font-medium text-text-primary">
            {isCancelling ? 'Stopping scan...' : 'Scanning files...'}
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
          {scanProgress.processed} / {scanProgress.total} files processed
        </span>
        {scanProgress.failed > 0 && (
          <span className="text-error">{scanProgress.failed} failed</span>
        )}
        <span>{progress}%</span>
      </div>
    </div>
  );
}
