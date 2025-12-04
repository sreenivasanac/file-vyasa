import { useEffect, useState, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';

interface ProcessingFile {
  path: string;
  filename: string;
}

/**
 * Hook for polling folder sync status and currently processing files.
 * Manages sync progress updates and detects completion.
 */
export function useSyncPolling(folderId: string | null, isSyncing: boolean) {
  const queryClient = useQueryClient();
  const { setSyncProgress, setIsSyncing, clearSyncTiming } = useAppStore();
  const [processingFiles, setProcessingFiles] = useState<ProcessingFile[]>([]);
  const clearSyncTimingRef = useRef(clearSyncTiming);

  useEffect(() => {
    clearSyncTimingRef.current = clearSyncTiming;
  }, [clearSyncTiming]);

  useEffect(() => {
    if (!folderId || !isSyncing) {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const [folder, processingData] = await Promise.all([
          api.folders.get(folderId),
          api.folders.getProcessing(folderId),
        ]);

        setSyncProgress({
          total: folder.total_files,
          processed: folder.processed_files,
          failed: folder.failed_files,
        });

        setProcessingFiles(processingData.processing_files);

        // Detect sync completion
        if (
          folder.status === 'idle' ||
          folder.status === 'error' ||
          folder.status === 'cancelled'
        ) {
          setIsSyncing(false);
          setProcessingFiles([]);
          clearSyncTimingRef.current();
          queryClient.invalidateQueries({ queryKey: ['folders'] });
          queryClient.invalidateQueries({ queryKey: ['files'] });
        }
      } catch (err) {
        console.error('Failed to poll folder status:', err);
      }
    }, 1000);

    return () => {
      clearInterval(pollInterval);
      setProcessingFiles([]);
    };
  }, [folderId, isSyncing, setSyncProgress, setIsSyncing, queryClient]);

  return { processingFiles };
}
