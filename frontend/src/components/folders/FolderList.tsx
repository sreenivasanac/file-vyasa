import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { openPath } from '@tauri-apps/plugin-opener';
import { Folder, Plus, ExternalLink } from 'lucide-react';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import { Spinner } from '@/components/common/Spinner';
import { Button } from '@/components/common/Button';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { FolderStatusBadge } from './FolderStatusBadge';
import { FolderInfoCard } from './FolderInfoCard';
import { truncatePath } from '@/lib/utils';
import type { MonitoredFolder } from '@/types';

export function FolderList() {
  const {
    setCurrentFolder,
    setCurrentView,
    setFolders,
    setIsSyncing,
    setSyncProgress,
  } = useAppStore();
  const queryClient = useQueryClient();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [folderToDelete, setFolderToDelete] = useState<string | null>(null);

  const {
    data: folders,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['folders'],
    queryFn: () => api.folders.list(),
    refetchInterval: (query) => {
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

  const handleSync = async (folderId: string) => {
    setSyncingId(folderId);
    try {
      await api.folders.sync(folderId);
      refetch();
    } catch (err) {
      console.error('Failed to sync folder:', err);
    } finally {
      setSyncingId(null);
    }
  };

  const handleOpenFolder = async (folderPath: string) => {
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
      <div className="flex h-full flex-col items-center justify-center p-8 text-text-muted">
        <Folder className="mb-3 h-16 w-16 opacity-50" />
        <p className="text-lg font-medium">No folders monitored yet</p>
        <p className="mt-1 text-sm">Add a folder to start organizing your files</p>
        <Button onClick={() => setCurrentView('add-folder')} className="mt-6">
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
            {/* Folder name and path header */}
            <div className="flex items-start justify-between">
              <div className="flex min-w-0 flex-1 items-start gap-3">
                <Folder className="mt-0.5 h-5 w-5 flex-shrink-0 text-accent" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-text-primary">{folder.name}</p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenFolder(folder.root_path);
                      }}
                      className="shrink-0 rounded p-1 text-text-muted hover:bg-bg-hover hover:text-text-primary"
                      title="Open in Finder"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </button>
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

            {/* Shared folder info card (compact mode) */}
            <FolderInfoCard
              folder={folder}
              onSync={() => handleSync(folder.id)}
              onDelete={() => setFolderToDelete(folder.id)}
              isSyncingAction={syncingId === folder.id}
              isDeleting={deletingId === folder.id}
              compact
            />
          </div>
        ))}
      </div>

      <ConfirmDialog
        isOpen={folderToDelete !== null}
        title="Remove Folder"
        message={
          <>
            Remove this folder from monitoring?{' '}
            <span className="font-medium text-text-primary">
              Your files will not be deleted.
            </span>
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
