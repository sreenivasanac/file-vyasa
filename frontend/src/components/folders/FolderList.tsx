import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { openPath } from '@tauri-apps/plugin-opener';
import {
  Folder,
  Clock,
  RefreshCw,
  Trash2,
  CheckCircle,
  Loader,
  AlertCircle,
  Plus,
  ExternalLink,
  Play,
} from 'lucide-react';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import { Spinner } from '@/components/common/Spinner';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { formatDate, truncatePath } from '@/lib/utils';
import type { FolderStatus, MonitoredFolder } from '@/types';

export function FolderList() {
  const { setCurrentFolder, setCurrentView, setFolders, setIsSyncing, setSyncProgress } =
    useAppStore();
  const queryClient = useQueryClient();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [folderToDelete, setFolderToDelete] = useState<string | null>(null);

  const { data: folders, isLoading, refetch } = useQuery({
    queryKey: ['folders'],
    queryFn: () => api.folders.list(),
    refetchInterval: (query) => {
      // Poll more frequently if any folder is syncing
      const data = query.state.data;
      if (data?.some((f) => f.status === 'syncing')) {
        return 2000;
      }
      return false;
    },
  });

  useEffect(() => {
    if (folders) {
      setFolders(folders);
    }
  }, [folders, setFolders]);

  const handleSelectFolder = (folder: MonitoredFolder) => {
    setCurrentFolder(folder.id, folder.root_path);
    if (folder.status === 'syncing') {
      setIsSyncing(true);
      setSyncProgress({
        total: folder.total_files,
        processed: folder.processed_files,
        failed: folder.failed_files,
      });
    }
    setCurrentView('files');
  };

  const handleSync = async (e: React.MouseEvent, folder: MonitoredFolder) => {
    e.stopPropagation();
    setSyncingId(folder.id);
    try {
      await api.folders.sync(folder.id);
      refetch();
    } catch (err) {
      console.error('Failed to sync folder:', err);
    } finally {
      setSyncingId(null);
    }
  };

  const handleDelete = (e: React.MouseEvent, folderId: string) => {
    e.stopPropagation();
    setFolderToDelete(folderId);
  };

  const handleOpenFolder = async (e: React.MouseEvent, folderPath: string) => {
    e.stopPropagation();
    try {
      await openPath(folderPath);
    } catch (err) {
      console.error('Failed to open folder:', err);
    }
  };

  const confirmDelete = async () => {
    if (!folderToDelete) return;
    setDeletingId(folderToDelete);
    setFolderToDelete(null);
    try {
      await api.folders.delete(folderToDelete);
      queryClient.invalidateQueries({ queryKey: ['folders'] });
    } catch (err) {
      console.error('Failed to delete folder:', err);
    } finally {
      setDeletingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" className="text-accent" />
      </div>
    );
  }

  if (!folders || folders.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-text-muted p-8">
        <Folder className="mb-3 h-16 w-16 opacity-50" />
        <p className="text-lg font-medium">No folders monitored yet</p>
        <p className="mt-1 text-sm">Add a folder to start organizing your files</p>
        <Button
          onClick={() => setCurrentView('add-folder')}
          className="mt-6"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Folder
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-text-primary">My Folders</h2>
        <Button onClick={() => setCurrentView('add-folder')} size="sm">
          <Plus className="mr-2 h-4 w-4" />
          Add Folder
        </Button>
      </div>

      <div className="space-y-3">
        {folders.map((folder) => (
          <div
            key={folder.id}
            onClick={() => handleSelectFolder(folder)}
            className="cursor-pointer rounded-lg border border-border bg-bg-secondary p-4 transition-colors hover:bg-bg-tertiary"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <Folder className="mt-0.5 h-5 w-5 flex-shrink-0 text-accent" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-text-primary">{folder.name}</p>
                    <button
                      onClick={(e) => handleOpenFolder(e, folder.root_path)}
                      className="shrink-0 rounded p-1 text-text-muted hover:bg-bg-hover hover:text-text-primary"
                      title="Open in Finder"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  <p
                    className="mt-0.5 text-xs text-text-muted truncate"
                    title={folder.root_path}
                  >
                    {truncatePath(folder.root_path, 60)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 ml-4">
                <StatusBadge status={folder.status} />
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
                <button
                  onClick={(e) => handleSync(e, folder)}
                  disabled={folder.status === 'syncing' || syncingId === folder.id}
                  className="flex items-center gap-1 rounded px-2 py-1 text-xs text-text-secondary hover:bg-bg-hover disabled:opacity-50"
                  title={folder.status === 'cancelled' ? 'Continue sync' : 'Sync folder'}
                >
                  {folder.status === 'cancelled' ? (
                    <Play className="h-3 w-3" />
                  ) : (
                    <RefreshCw
                      className={`h-3 w-3 ${
                        folder.status === 'syncing' || syncingId === folder.id
                          ? 'animate-spin'
                          : ''
                      }`}
                    />
                  )}
                  {folder.status === 'cancelled' ? 'Continue' : 'Sync'}
                </button>
                <button
                  onClick={(e) => handleDelete(e, folder.id)}
                  disabled={deletingId === folder.id}
                  className="flex items-center gap-1 rounded px-2 py-1 text-xs text-error hover:bg-error/10 disabled:opacity-50"
                  title="Remove folder"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>

            {folder.status === 'syncing' && (
              <div className="mt-3">
                <div className="h-1.5 overflow-hidden rounded-full bg-bg-tertiary">
                  <div
                    className="h-full bg-accent transition-all duration-300"
                    style={{
                      width: `${
                        folder.total_files > 0
                          ? Math.round((folder.processed_files / folder.total_files) * 100)
                          : 0
                      }%`,
                    }}
                  />
                </div>
                <p className="mt-1 text-xs text-text-muted">
                  {folder.processed_files} / {folder.total_files} files processed
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      <ConfirmDialog
        isOpen={folderToDelete !== null}
        title="Remove Folder"
        message={
          <>
            Remove this folder from monitoring?{' '}
            <span className="font-medium text-text-primary">Your files will not be deleted.</span>
          </>
        }
        confirmText="Remove"
        cancelText="Cancel"
        variant="danger"
        onConfirm={confirmDelete}
        onCancel={() => setFolderToDelete(null)}
      />
    </div>
  );
}

function StatusBadge({ status }: { status: FolderStatus }) {
  switch (status) {
    case 'idle':
      return (
        <Badge variant="success">
          <CheckCircle className="mr-1 h-3 w-3" />
          Ready
        </Badge>
      );
    case 'syncing':
      return (
        <Badge variant="info">
          <Loader className="mr-1 h-3 w-3 animate-spin" />
          Syncing
        </Badge>
      );
    case 'error':
      return (
        <Badge variant="error">
          <AlertCircle className="mr-1 h-3 w-3" />
          Error
        </Badge>
      );
    case 'cancelled':
      return (
        <Badge variant="warning">
          Cancelled
        </Badge>
      );
    default:
      return <Badge>{status}</Badge>;
  }
}
