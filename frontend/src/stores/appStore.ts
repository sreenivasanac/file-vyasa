import { create } from 'zustand';
import type { FileObject, MonitoredFolder } from '@/types';

type View = 'add-folder' | 'folders' | 'files' | 'settings';

interface AppState {
  // Navigation
  currentView: View;
  setCurrentView: (view: View) => void;

  // Folder state
  currentFolderId: string | null;
  currentFolderPath: string | null;
  isSyncing: boolean;
  syncProgress: {
    total: number;
    processed: number;
    failed: number;
  };
  setCurrentFolder: (folderId: string | null, path: string | null) => void;
  setIsSyncing: (isSyncing: boolean) => void;
  setSyncProgress: (progress: { total: number; processed: number; failed: number }) => void;

  // Files state
  selectedFileId: string | null;
  setSelectedFileId: (fileId: string | null) => void;
  selectedFile: FileObject | null;
  setSelectedFile: (file: FileObject | null) => void;

  // Folders list
  folders: MonitoredFolder[];
  setFolders: (folders: MonitoredFolder[]) => void;

  // Backend status
  backendConnected: boolean;
  setBackendConnected: (connected: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Navigation
  currentView: 'folders',
  setCurrentView: (view) => set({ currentView: view }),

  // Folder state
  currentFolderId: null,
  currentFolderPath: null,
  isSyncing: false,
  syncProgress: { total: 0, processed: 0, failed: 0 },
  setCurrentFolder: (folderId, path) =>
    set({ currentFolderId: folderId, currentFolderPath: path }),
  setIsSyncing: (isSyncing) => set({ isSyncing }),
  setSyncProgress: (progress) => set({ syncProgress: progress }),

  // Files state
  selectedFileId: null,
  setSelectedFileId: (fileId) => set({ selectedFileId: fileId }),
  selectedFile: null,
  setSelectedFile: (file) => set({ selectedFile: file }),

  // Folders list
  folders: [],
  setFolders: (folders) => set({ folders }),

  // Backend status
  backendConnected: false,
  setBackendConnected: (connected) => set({ backendConnected: connected }),
}));
