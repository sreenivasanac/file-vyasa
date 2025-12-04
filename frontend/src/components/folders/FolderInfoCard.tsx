import { Clock, RefreshCw, Trash2, Play, ExternalLink } from 'lucide-react';
import { FolderStatusBadge } from './FolderStatusBadge';
import { SyncProgressBar } from '@/components/common/SyncProgressBar';
import { formatDate } from '@/lib/utils';
import type { MonitoredFolder } from '@/types';

interface FolderInfoCardProps {
  folder: MonitoredFolder;
  onSync: () => void;
  onDelete: () => void;
  onOpenInFinder?: () => void;
  isSyncingAction: boolean;
  isDeleting?: boolean;
  compact?: boolean;
}

/**
 * Shared folder info card used in both FolderList (compact) and FileList header.
 */
export function FolderInfoCard({
  folder,
  onSync,
  onDelete,
  onOpenInFinder,
  isSyncingAction,
  isDeleting = false,
  compact = false,
}: FolderInfoCardProps) {
  const isSyncDisabled = folder.status === 'syncing' || isSyncingAction;
  const showContinue = folder.status === 'cancelled';

  if (compact) {
    // Compact mode for FolderList rows
    return (
      <div className="w-full">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FolderStatusBadge status={folder.status} />
          </div>
        </div>

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
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSync();
              }}
              disabled={isSyncDisabled}
              className="flex items-center gap-1 rounded px-2 py-1 text-xs text-text-secondary hover:bg-bg-hover disabled:opacity-50"
              title={showContinue ? 'Continue sync' : 'Sync folder'}
            >
              {showContinue ? (
                <Play className="h-3 w-3" />
              ) : (
                <RefreshCw
                  className={`h-3 w-3 ${isSyncDisabled ? 'animate-spin' : ''}`}
                />
              )}
              {showContinue ? 'Continue' : 'Sync'}
            </button>
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
          </div>
        </div>

        {folder.status === 'syncing' && (
          <div className="mt-3">
            <SyncProgressBar
              total={folder.total_files}
              processed={folder.processed_files}
              size="sm"
            />
            <p className="mt-1 text-xs text-text-muted">
              {folder.processed_files} / {folder.total_files} files processed
            </p>
          </div>
        )}
      </div>
    );
  }

  // Full header mode for FileList
  return (
    <div className="border-b border-border bg-bg-secondary px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-text-primary">{folder.name}</h2>
          <FolderStatusBadge status={folder.status} />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onSync}
            disabled={isSyncDisabled}
            className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-text-secondary hover:bg-bg-tertiary disabled:opacity-50"
            title={showContinue ? 'Continue sync' : 'Sync folder'}
          >
            {showContinue ? (
              <Play className="h-4 w-4" />
            ) : (
              <RefreshCw
                className={`h-4 w-4 ${isSyncDisabled ? 'animate-spin' : ''}`}
              />
            )}
            {showContinue ? 'Continue' : 'Sync'}
          </button>
          <button
            onClick={onDelete}
            disabled={isDeleting}
            className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-error hover:bg-error/10 disabled:opacity-50"
            title="Remove folder"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="mt-2 flex items-center gap-4 text-xs text-text-muted">
        <span>{folder.total_files} files</span>
        {folder.last_synced_at && (
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Last synced: {formatDate(folder.last_synced_at)}
          </span>
        )}
        {folder.last_llm_model && <span>Model: {folder.last_llm_model}</span>}
      </div>
    </div>
  );
}
