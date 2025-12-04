import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import { FileFilters } from './FileFilters';
import { FolderTree } from './FolderTree';
import { SyncProgress } from '@/components/folders/SyncProgress';
import { FolderInfoCard } from '@/components/folders/FolderInfoCard';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { Spinner } from '@/components/common/Spinner';
import type { FileCategory } from '@/types';

export function FileList() {
  const {
    currentFolderId,
    currentFolderPath,
    isSyncing,
    syncProgress,
    selectedFileId,
    setSelectedFileId,
    folders,
    setCurrentFolder,
    setCurrentView,
  } = useAppStore();
  const queryClient = useQueryClient();

  const [category, setCategory] = useState<FileCategory | undefined>();
  const [search, setSearch] = useState('');
  const [isSyncingFolder, setIsSyncingFolder] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const pageSize = 500;

  const currentFolder = folders.find((f) => f.id === currentFolderId);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['files', currentFolderId, category, search],
    queryFn: () =>
      api.files.list({
        folder_id: currentFolderId || undefined,
        category,
        search: search || undefined,
        page: 1,
        page_size: pageSize,
      }),
    enabled: !!currentFolderId,
    refetchInterval: isSyncing ? 2000 : false,
  });

  useEffect(() => {
    if (!isSyncing) {
      refetch();
    }
  }, [isSyncing, refetch]);

  const handleSync = async () => {
    if (!currentFolderId) return;
    setIsSyncingFolder(true);
    try {
      await api.folders.sync(currentFolderId);
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      refetch();
    } catch (err) {
      console.error('Failed to sync folder:', err);
    } finally {
      setIsSyncingFolder(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!currentFolderId) return;
    setIsDeleting(true);
    setShowDeleteConfirm(false);
    try {
      await api.folders.delete(currentFolderId);
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      setCurrentFolder(null, null);
      setCurrentView('folders');
    } catch (err) {
      console.error('Failed to delete folder:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  if (!currentFolderId) {
    return (
      <div className="flex h-full items-center justify-center text-text-muted">
        Select a folder from My Folders first
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Shared Folder Info Header */}
      {currentFolder && (
        <FolderInfoCard
          folder={currentFolder}
          onSync={handleSync}
          onDelete={() => setShowDeleteConfirm(true)}
          isSyncingAction={isSyncingFolder}
          isDeleting={isDeleting}
        />
      )}

      <div className="border-b border-border p-4">
        <SyncProgress />
        <div className="mt-4">
          <FileFilters
            category={category}
            onCategoryChange={setCategory}
            search={search}
            onSearchChange={setSearch}
          />
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {isLoading && !isSyncing ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner size="lg" className="text-accent" />
          </div>
        ) : data?.files.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center gap-3 text-text-muted">
            {isSyncing ? (
              <>
                <Spinner size="lg" className="text-accent" />
                <span>Syncing files... Files will appear as they are processed.</span>
              </>
            ) : (
              'No files found'
            )}
          </div>
        ) : currentFolderPath ? (
          <FolderTree
            files={data?.files || []}
            rootPath={currentFolderPath}
            selectedFileId={selectedFileId}
            onSelectFile={setSelectedFileId}
            isSyncing={isSyncing}
            totalFiles={isSyncing ? syncProgress.total : currentFolder?.total_files}
            processedFiles={isSyncing ? syncProgress.processed : currentFolder?.processed_files}
          />
        ) : null}
      </div>

      <div className="border-t border-border px-4 py-2 text-xs text-text-muted">
        {(isSyncing ? syncProgress.total : currentFolder?.total_files) ??
          data?.total ??
          0}{' '}
        files total
      </div>

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Remove Folder"
        message={
          <>
            Remove this folder from monitoring?{' '}
            <span className="font-medium text-text-primary">
              Your files will not be deleted.
            </span>
          </>
        }
        confirmText="Yes"
        cancelText="Cancel"
        variant="danger"
        onConfirm={handleConfirmDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
