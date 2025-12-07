import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { openPath } from '@tauri-apps/plugin-opener';
import { Folder, Plus } from 'lucide-react';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import { useFolderActions } from '@/hooks/useFolderActions';
import { Spinner } from '@/components/common/Spinner';
import { Button } from '@/components/common/Button';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { FolderInfoCard } from './FolderInfoCard';
import type { MonitoredFolder } from '@/types';

export function FolderList() {
  const {
    setCurrentFolder,
    setCurrentView,
    setFolders,
    setIsSyncing,
    setSyncProgress,
    updateFolder,
  } = useAppStore();
  const queryClient = useQueryClient();

  const [folderToDelete, setFolderToDelete] = useState<string | null>(null);
  const [activeFolderId, setActiveFolderId] = useState<string | null>(null);

  // Use shared hook for folder actions (only for delete)
  const { deleteFolder, isDeleting } = useFolderActions(activeFolderId, {
    onAfterDelete: () => setFolderToDelete(null),
  });
  const [isSyncingFolder, setIsSyncingFolder] = useState(false);

  const { data: folders, isLoading } = useQuery({
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
    } else if (folder.status === 'cancelled') {
      setIsSyncing(false);
      setSyncProgress({
        total: folder.total_files,
        processed: folder.processed_files,
        failed: folder.failed_files,
      });
    }
    setCurrentView('files');
  };

  const handleSync = async (folderId: string) => {
    if (isSyncingFolder) return;
    setActiveFolderId(folderId);
    setIsSyncingFolder(true);
    try {
      const folder = await api.folders.sync(folderId);
      updateFolder(folder);
      setIsSyncing(folder.status === 'syncing');
      setSyncProgress({
        total: folder.total_files,
        processed: folder.processed_files,
        failed: folder.failed_files,
      });
      queryClient.invalidateQueries({ queryKey: ['folders'] });
    } catch (err) {
      console.error('Failed to sync folder:', err);
      setIsSyncing(false);
    } finally {
      setIsSyncingFolder(false);
    }
  };

  const handleOpenFolder = async (folderPath: string) => {
    try {
      await openPath(folderPath);
    } catch (err) {
      console.error('Failed to open folder:', err);
    }
  };

  const handleDeleteClick = (folderId: string) => {
    setActiveFolderId(folderId);
    setFolderToDelete(folderId);
  };

  const confirmDelete = async () => {
    await deleteFolder();
    setFolderToDelete(null);
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
            <FolderInfoCard
              folder={folder}
              onSync={() => handleSync(folder.id)}
              onDelete={() => handleDeleteClick(folder.id)}
              onOpenInFinder={() => handleOpenFolder(folder.root_path)}
              isSyncingAction={activeFolderId === folder.id && isSyncingFolder}
              isDeleting={activeFolderId === folder.id && isDeleting}
              showFolderDetails
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
