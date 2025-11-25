import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Folder, Clock, CheckCircle, XCircle, Loader } from 'lucide-react';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import { Spinner } from '@/components/common/Spinner';
import { Badge } from '@/components/common/Badge';
import { formatDate, truncatePath } from '@/lib/utils';
import type { ScanStatus } from '@/types';

export function RecentScans() {
  const { setCurrentScan, setCurrentView, setRecentScans } = useAppStore();

  const { data: scans, isLoading } = useQuery({
    queryKey: ['recent-scans'],
    queryFn: () => api.scan.recent(20),
  });

  useEffect(() => {
    if (scans) {
      setRecentScans(scans);
    }
  }, [scans, setRecentScans]);

  const handleSelectScan = (scanId: string, rootPath: string) => {
    setCurrentScan(scanId, rootPath);
    setCurrentView('files');
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" className="text-accent" />
      </div>
    );
  }

  if (!scans || scans.length === 0) {
    return (
      <div className="flex h-64 flex-col items-center justify-center text-text-muted">
        <Clock className="mb-3 h-12 w-12" />
        <p>No recent scans</p>
        <p className="mt-1 text-sm">Start a scan to see it here</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="mb-4 text-xl font-semibold text-text-primary">
        Recent Scans
      </h2>

      <div className="space-y-3">
        {scans.map((scan) => (
          <div
            key={scan.scan_id}
            onClick={() => handleSelectScan(scan.scan_id, scan.root_path)}
            className="cursor-pointer rounded-lg border border-border bg-bg-secondary p-4 transition-colors hover:bg-bg-tertiary"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <Folder className="mt-0.5 h-5 w-5 text-accent" />
                <div>
                  <p
                    className="font-medium text-text-primary"
                    title={scan.root_path}
                  >
                    {truncatePath(scan.root_path, 50)}
                  </p>
                  <p className="mt-1 text-xs text-text-muted">
                    {formatDate(scan.started_at)}
                  </p>
                </div>
              </div>
              <StatusBadge status={scan.status} />
            </div>

            <div className="mt-3 flex items-center gap-4 text-xs text-text-muted">
              <span>{scan.total_files} files</span>
              <span>{scan.processed_files} processed</span>
              {scan.failed_files > 0 && (
                <span className="text-error">{scan.failed_files} failed</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: ScanStatus }) {
  switch (status) {
    case 'completed':
      return (
        <Badge variant="success">
          <CheckCircle className="mr-1 h-3 w-3" />
          Completed
        </Badge>
      );
    case 'in_progress':
      return (
        <Badge variant="info">
          <Loader className="mr-1 h-3 w-3 animate-spin" />
          In Progress
        </Badge>
      );
    case 'failed':
      return (
        <Badge variant="error">
          <XCircle className="mr-1 h-3 w-3" />
          Failed
        </Badge>
      );
    default:
      return <Badge>{status}</Badge>;
  }
}
