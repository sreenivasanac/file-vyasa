import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';

interface UseFolderActionsOptions {
  onAfterSync?: () => void;
  onAfterDelete?: () => void;
}

/**
 * Hook for folder sync/delete actions with shared state management.
 */
export function useFolderActions(
  folderId: string | null,
  options: UseFolderActionsOptions = {}
) {
  const queryClient = useQueryClient();
  const [isSyncing, setIsSyncing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const { setIsSyncing: setGlobalSyncing, setSyncProgress, updateFolder } = useAppStore();

  const syncFolder = useCallback(async () => {
    if (!folderId || isSyncing) return;
    setIsSyncing(true);
    setGlobalSyncing(true);
    try {
      const folder = await api.folders.sync(folderId);
      setSyncProgress({
        total: folder.total_files,
        processed: folder.processed_files,
        failed: folder.failed_files,
      });
      updateFolder(folder);
      setGlobalSyncing(folder.status === 'syncing');
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      options.onAfterSync?.();
    } catch (err) {
      console.error('Failed to sync folder:', err);
      setGlobalSyncing(false);
    } finally {
      setIsSyncing(false);
    }
  }, [folderId, isSyncing, queryClient, options, setGlobalSyncing, setSyncProgress, updateFolder]);

  const deleteFolder = useCallback(async () => {
    if (!folderId || isDeleting) return;
    setIsDeleting(true);
    try {
      await api.folders.delete(folderId);
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      options.onAfterDelete?.();
    } catch (err) {
      console.error('Failed to delete folder:', err);
    } finally {
      setIsDeleting(false);
    }
  }, [folderId, isDeleting, queryClient, options]);

  return { syncFolder, deleteFolder, isSyncing, isDeleting };
}
