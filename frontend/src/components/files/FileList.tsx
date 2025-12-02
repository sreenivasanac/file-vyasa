import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  RefreshCw,
  Trash2,
  Clock,
  CheckCircle,
  Loader,
  AlertCircle,
  Play,
} from 'lucide-react';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import { FileFilters } from './FileFilters';
import { FolderTree } from './FolderTree';
import { SyncProgress } from '@/components/folders/SyncProgress';
import { Badge } from '@/components/common/Badge';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { Spinner } from '@/components/common/Spinner';
import { formatDate } from '@/lib/utils';
import type { FileCategory, FolderStatus } from '@/types';

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
  const pageSize = 500; // Larger page size for tree view

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

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
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

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
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
      {/* Folder Info Header */}
      {currentFolder && (
        <div className="border-b border-border bg-bg-secondary px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold text-text-primary">
                {currentFolder.name}
              </h2>
              <StatusBadge status={currentFolder.status} />
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleSync}
                disabled={currentFolder.status === 'syncing' || isSyncingFolder}
                className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-text-secondary hover:bg-bg-tertiary disabled:opacity-50"
                title={currentFolder.status === 'cancelled' ? 'Continue sync' : 'Sync folder'}
              >
                {currentFolder.status === 'cancelled' ? (
                  <Play className="h-4 w-4" />
                ) : (
                  <RefreshCw
                    className={`h-4 w-4 ${
                      currentFolder.status === 'syncing' || isSyncingFolder
                        ? 'animate-spin'
                        : ''
                    }`}
                  />
                )}
                {currentFolder.status === 'cancelled' ? 'Continue' : 'Sync'}
              </button>
              <button
                onClick={handleDeleteClick}
                disabled={isDeleting}
                className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-error hover:bg-error/10 disabled:opacity-50"
                title="Remove folder"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="mt-2 flex items-center gap-4 text-xs text-text-muted">
            <span>{currentFolder.total_files} files</span>
            {currentFolder.last_synced_at && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Last synced: {formatDate(currentFolder.last_synced_at)}
              </span>
            )}
            {currentFolder.last_llm_model && (
              <span>Model: {currentFolder.last_llm_model}</span>
            )}
          </div>
        </div>
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
        {(isSyncing ? syncProgress.total : currentFolder?.total_files) ?? data?.total ?? 0} files total
      </div>

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Remove Folder"
        message={
          <>
            Remove this folder from monitoring?{' '}
            <span className="font-medium text-text-primary">Your files will not be deleted.</span>
          </>
        }
        confirmText="Yes"
        cancelText="Cancel"
        variant="danger"
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
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
