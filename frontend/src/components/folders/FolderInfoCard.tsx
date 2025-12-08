import { Folder, Clock, RefreshCw, Trash2, Play, Square, ExternalLink } from 'lucide-react';
import { FolderStatusBadge } from './FolderStatusBadge';
import { SyncProgressBar } from '@/components/common/SyncProgressBar';
import { formatDate, truncatePath } from '@/lib/utils';
import { type SyncProgressData, computeEtaLabel } from '@/lib/syncUtils';
import type { MonitoredFolder } from '@/types';

interface FolderInfoCardProps {
  folder: MonitoredFolder;
  onSync?: () => void;
  onDelete?: () => void;
  onCancel?: () => void;
  onOpenInFinder?: () => void;
  isSyncingAction?: boolean;
  isDeleting?: boolean;
  isCancelling?: boolean;
  /** Sync progress data for ETA calculation (only when syncing) */
  syncProgress?: SyncProgressData;
  /** Wrap content in a styled container with border/background */
  asHeader?: boolean;
}

/**
 * Unified folder info component with identical layout for FolderList and FileList.
 * Handles syncing state with Stop button, progress bar, and ETA display.
 */
export function FolderInfoCard({
  folder,
  onSync,
  onDelete,
  onCancel,
  onOpenInFinder,
  isSyncingAction,
  isDeleting = false,
  isCancelling = false,
  syncProgress,
  asHeader = false,
}: FolderInfoCardProps) {
  const isSyncing = folder.status === 'syncing';
  const isCancelled = folder.status === 'cancelled';

  // Use syncProgress data when available, otherwise use folder data
  const displayTotal = syncProgress?.total ?? folder.total_files;
  const displayProcessed = syncProgress?.processed ?? folder.processed_files;
  const displayFailed = syncProgress?.failed ?? folder.failed_files;
  const eta = syncProgress ? computeEtaLabel(syncProgress) : null;

  const content = (
    <div className="w-full">
      {/* Row 1: folder icon, name, external link, status badge */}
      <div className="flex items-start justify-between">
        <div className="flex min-w-0 flex-1 items-start gap-3">
          <Folder className="mt-0.5 h-5 w-5 flex-shrink-0 text-accent" />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className="font-medium text-text-primary">{folder.name}</p>
              {onOpenInFinder && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onOpenInFinder();
                  }}
                  className="shrink-0 rounded p-1 text-text-muted hover:bg-bg-hover hover:text-text-primary"
                  title="Open in Finder"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
            <p
              className="mt-0.5 truncate text-xs text-text-muted"
              title={folder.root_path}
            >
              {truncatePath(folder.root_path, 60)}
            </p>
          </div>
        </div>
        <div className="ml-4 flex items-center gap-2">
          <FolderStatusBadge status={folder.status} />
        </div>
      </div>

      {/* Row 2: Metadata + actions */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs text-text-muted">
          <span>{folder.total_files} files</span>
          {folder.last_synced_at && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDate(folder.last_synced_at)}
            </span>
          )}
          {folder.last_llm_model && (
            <span className="text-text-muted/70">{folder.last_llm_model}</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Sync/Stop/Continue button */}
          {isSyncing ? (
            onCancel && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onCancel();
                }}
                disabled={isCancelling}
                className="flex items-center gap-1 rounded px-2 py-1 text-xs text-error hover:bg-error/10 disabled:opacity-50"
                title="Stop sync"
              >
                <Square className="h-3 w-3" />
                {isCancelling ? 'Stopping...' : 'Stop'}
              </button>
            )
          ) : (
            onSync && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSync();
                }}
                disabled={isSyncingAction}
                className="flex items-center gap-1 rounded px-2 py-1 text-xs text-text-secondary hover:bg-bg-hover disabled:opacity-50"
                title={isCancelled ? 'Continue sync' : 'Sync folder'}
              >
                {isCancelled ? (
                  <Play className="h-3 w-3" />
                ) : (
                  <RefreshCw
                    className={`h-3 w-3 ${isSyncingAction ? 'animate-spin' : ''}`}
                  />
                )}
                {isCancelled ? 'Continue' : 'Sync'}
              </button>
            )
          )}
          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              disabled={isDeleting}
              className="flex items-center gap-1 rounded px-2 py-1 text-xs text-error hover:bg-error/10 disabled:opacity-50"
              title="Remove folder"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {/* Row 3: Progress bar when syncing or cancelled */}
      {(isSyncing || isCancelled) && (
        <div className="mt-3">
          <SyncProgressBar
            total={displayTotal}
            processed={displayProcessed}
            variant={isCancelled ? 'warning' : 'accent'}
            size="sm"
          />
          <div className="mt-1 flex items-center justify-between text-xs text-text-muted">
            <span>
              {displayProcessed}/{displayTotal} files processed
              {eta && <span className="ml-2 text-text-secondary">{eta}</span>}
            </span>
            {displayFailed > 0 && (
              <span className="text-error">{displayFailed} failed</span>
            )}
          </div>
        </div>
      )}
    </div>
  );

  if (asHeader) {
    return (
      <div className="border-b border-border bg-bg-secondary px-4 py-3">
        {content}
      </div>
    );
  }

  return content;
}
