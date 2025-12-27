import { useEffect, useState, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import type { FolderStatus } from '@/types';

interface ProcessingFile {
  path: string;
  filename: string;
}

const POLL_INTERVAL_MS = 5000;

/**
 * Hook for polling folder sync status and currently processing files.
 * Manages sync progress updates and detects completion.
 */
export function useSyncPolling(
  folderId: string | null,
  isSyncing: boolean,
  folderStatus?: FolderStatus
) {
  const queryClient = useQueryClient();
  const { setSyncProgress, setIsSyncing, clearSyncTiming, updateFolder } = useAppStore();
  const [processingFiles, setProcessingFiles] = useState<ProcessingFile[]>([]);

  // Use refs for callbacks to avoid recreating the interval on every render
  const setSyncProgressRef = useRef(setSyncProgress);
  const setIsSyncingRef = useRef(setIsSyncing);
  const clearSyncTimingRef = useRef(clearSyncTiming);
  const updateFolderRef = useRef(updateFolder);

  useEffect(() => {
    setSyncProgressRef.current = setSyncProgress;
    setIsSyncingRef.current = setIsSyncing;
    clearSyncTimingRef.current = clearSyncTiming;
    updateFolderRef.current = updateFolder;
  }, [setSyncProgress, setIsSyncing, clearSyncTiming, updateFolder]);

  useEffect(() => {
    const shouldPoll = !!folderId && (isSyncing || folderStatus === 'syncing');
    if (!shouldPoll) {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        // Single API call for both folder status and processing files
        const { folder, processing_files } = await api.folders.getSyncStatus(folderId);

        setSyncProgressRef.current({
          total: folder.total_files,
          processed: folder.processed_files,
          failed: folder.failed_files,
        });

        updateFolderRef.current(folder);
        setProcessingFiles(processing_files);

        setIsSyncingRef.current(folder.status === 'syncing');

        // Invalidate files query during sync to show newly processed files
        if (folder.status === 'syncing') {
          queryClient.invalidateQueries({ queryKey: ['files'] });
        }

        // Detect sync completion
        if (
          folder.status === 'idle' ||
          folder.status === 'error' ||
          folder.status === 'cancelled'
        ) {
          setIsSyncingRef.current(false);
          setProcessingFiles([]);
          clearSyncTimingRef.current();
          queryClient.invalidateQueries({ queryKey: ['folders'] });
          queryClient.invalidateQueries({ queryKey: ['files'] });
        }
      } catch (err) {
        console.error('Failed to poll folder status:', err);
      }
    }, POLL_INTERVAL_MS);

    return () => {
      clearInterval(pollInterval);
      setProcessingFiles([]);
    };
  }, [folderId, isSyncing, folderStatus, queryClient]);

  return { processingFiles };
}
