import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';

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

  const syncFolder = useCallback(async () => {
    if (!folderId || isSyncing) return;
    setIsSyncing(true);
    try {
      await api.folders.sync(folderId);
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      options.onAfterSync?.();
    } catch (err) {
      console.error('Failed to sync folder:', err);
    } finally {
      setIsSyncing(false);
    }
  }, [folderId, isSyncing, queryClient, options]);

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
