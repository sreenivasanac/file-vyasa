import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import { useFolderActions } from '@/hooks/useFolderActions';
import { useSyncPolling } from '@/hooks/useSyncPolling';
import { openPath } from '@tauri-apps/plugin-opener';
import { FileFilters } from './FileFilters';
import { FolderTree } from './FolderTree';
import { FolderInfoCard } from '@/components/folders/FolderInfoCard';
import { BackendDisconnected } from '@/components/common/BackendDisconnected';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { Spinner } from '@/components/common/Spinner';
import type { ExtractionStatus, FileCategory, FilenameQuality } from '@/types';

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
    setIsSyncing,
    setSyncProgress,
    updateFolder,
    backendConnected,
    backendChecked,
  } = useAppStore();

  const [categories, setCategories] = useState<FileCategory[]>([]);
  const [extractionStatus, setExtractionStatus] = useState<ExtractionStatus | undefined>();
  const [filenameQuality, setFilenameQuality] = useState<FilenameQuality | undefined>();
  const [search, setSearch] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const pageSize = 500;

  const currentFolder = folders.find((f) => f.id === currentFolderId);

  // Use shared hook for folder actions
  const { syncFolder, deleteFolder, isSyncing: isSyncingAction, isDeleting } =
    useFolderActions(currentFolderId, {
      onAfterSync: () => refetch(),
      onAfterDelete: () => {
        setCurrentFolder(null, null);
        setCurrentView('folders');
      },
    });

  // Use sync polling to get currently processing files
  const { processingFiles } = useSyncPolling(currentFolderId, isSyncing, currentFolder?.status);
  const processingFilePaths = processingFiles.map((f) => f.path);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['files', currentFolderId, categories, extractionStatus, filenameQuality, search],
    queryFn: () =>
      api.files.list({
        folder_id: currentFolderId || undefined,
        categories: categories.length > 0 ? categories : undefined,
        extraction_status: extractionStatus,
        filename_quality: filenameQuality,
        search: search || undefined,
        page: 1,
        page_size: pageSize,
      }),
    enabled: !!currentFolderId,
  });

  // Seed sync state when a folder is selected
  useEffect(() => {
    if (!currentFolder) return;

    if (currentFolder.status === 'syncing') {
      setIsSyncing(true);
      setSyncProgress({
        total: currentFolder.total_files,
        processed: currentFolder.processed_files,
        failed: currentFolder.failed_files,
      });
    } else if (currentFolder.status === 'cancelled') {
      setIsSyncing(false);
      setSyncProgress({
        total: currentFolder.total_files,
        processed: currentFolder.processed_files,
        failed: currentFolder.failed_files,
      });
    }
  }, [currentFolder, setIsSyncing, setSyncProgress]);

  // Refetch files when sync completes
  useEffect(() => {
    if (!isSyncing) {
      refetch();
    }
  }, [isSyncing, refetch]);

  // Reset cancelling state when sync stops (deferred to avoid sync setState in effect)
  useEffect(() => {
    if (!isSyncing && isCancelling) {
      const timeout = setTimeout(() => setIsCancelling(false), 0);
      return () => clearTimeout(timeout);
    }
  }, [isSyncing, isCancelling]);

  const handleCancel = async () => {
    if (!currentFolderId || isCancelling) return;
    setIsCancelling(true);
    try {
      await api.folders.cancel(currentFolderId);
      const updated = await api.folders.get(currentFolderId);
      updateFolder(updated);
      setSyncProgress({
        total: updated.total_files,
        processed: updated.processed_files,
        failed: updated.failed_files,
      });
      setIsSyncing(false);
    } catch (err) {
      console.error('Failed to cancel sync:', err);
      setIsCancelling(false);
    }
  };

  const handleConfirmDelete = async () => {
    setShowDeleteConfirm(false);
    await deleteFolder();
  };

  // Show loading while checking backend connection
  if (!backendChecked) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" className="text-accent" />
      </div>
    );
  }

  if (!backendConnected) {
    return <BackendDisconnected />;
  }

  if (!currentFolderId) {
    return (
      <div className="flex h-full items-center justify-center text-text-muted">
        Select a folder from My Folders first
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Folder Info Header with integrated sync progress */}
      {currentFolder && (
        <FolderInfoCard
          folder={currentFolder}
          onSync={backendConnected ? syncFolder : undefined}
          onDelete={backendConnected ? () => setShowDeleteConfirm(true) : undefined}
          onCancel={backendConnected ? handleCancel : undefined}
          onOpenInFinder={() => currentFolder.root_path && openPath(currentFolder.root_path)}
          isSyncingAction={isSyncingAction}
          isDeleting={isDeleting}
          isCancelling={isCancelling}
          syncProgress={isSyncing ? syncProgress : undefined}
          asHeader
        />
      )}

      <div className="border-b border-border p-4">
        <FileFilters
          categories={categories}
          onCategoriesChange={setCategories}
          extractionStatus={extractionStatus}
          onExtractionStatusChange={setExtractionStatus}
          filenameQuality={filenameQuality}
          onFilenameQualityChange={setFilenameQuality}
          search={search}
          onSearchChange={setSearch}
        />
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
            processingFilePaths={processingFilePaths}
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
            Stop tracking this folder?{' '}
            <span className="font-medium text-text-primary">
              Your original files will remain safe on your device.
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
