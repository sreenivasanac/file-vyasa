import { useEffect } from 'react';
import { Spinner } from '@/components/common/Spinner';
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

        if (status.status === 'completed' || status.status === 'failed') {
          setIsScanning(false);
        }
      } catch (err) {
        console.error('Failed to poll scan status:', err);
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [currentScanId, isScanning, setScanProgress, setIsScanning]);

  if (!isScanning) return null;

  const progress =
    scanProgress.total > 0
      ? Math.round((scanProgress.processed / scanProgress.total) * 100)
      : 0;

  return (
    <div className="rounded-lg border border-border bg-bg-secondary p-4">
      <div className="mb-3 flex items-center gap-3">
        <Spinner size="sm" className="text-accent" />
        <span className="text-sm font-medium text-text-primary">
          Scanning files...
        </span>
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
