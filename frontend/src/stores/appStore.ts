import { create } from 'zustand';
import type { FileObject, MonitoredFolder } from '@/types';

type View = 'add-folder' | 'folders' | 'files' | 'settings';

interface AppState {
  // App config
  appName: string;
  setAppName: (name: string) => void;

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
    startTime: number | null;
    lastProcessedTime: number | null;
    processingTimes: number[];
  };
  setCurrentFolder: (folderId: string | null, path: string | null) => void;
  setIsSyncing: (isSyncing: boolean) => void;
  setSyncProgress: (progress: { total: number; processed: number; failed: number }) => void;
  clearSyncTiming: () => void;

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
  // App config
  appName: 'FileVyasa',
  setAppName: (name) => set({ appName: name }),

  // Navigation
  currentView: 'folders',
  setCurrentView: (view) => set({ currentView: view }),

  // Folder state
  currentFolderId: null,
  currentFolderPath: null,
  isSyncing: false,
  syncProgress: { total: 0, processed: 0, failed: 0, startTime: null, lastProcessedTime: null, processingTimes: [] },
  setCurrentFolder: (folderId, path) =>
    set({ currentFolderId: folderId, currentFolderPath: path }),
  setIsSyncing: (isSyncing) => set({ isSyncing }),
  setSyncProgress: (progress) => set((state) => {
    const now = Date.now();
    const prev = state.syncProgress;
    
    // Initialize start time on first progress update
    const startTime = prev.startTime ?? now;
    
    // Calculate time for newly processed files
    let processingTimes = [...prev.processingTimes];
    let lastProcessedTime = prev.lastProcessedTime ?? now;
    
    const newlyProcessed = progress.processed - prev.processed;
    if (newlyProcessed > 0 && prev.lastProcessedTime !== null) {
      const elapsed = now - prev.lastProcessedTime;
      const avgTimePerNewFile = elapsed / newlyProcessed;
      // Add time entries for each newly processed file
      for (let i = 0; i < newlyProcessed; i++) {
        processingTimes.push(avgTimePerNewFile);
      }
      // Keep only last 20 entries for moving average
      if (processingTimes.length > 20) {
        processingTimes = processingTimes.slice(-20);
      }
      lastProcessedTime = now;
    } else if (newlyProcessed > 0) {
      lastProcessedTime = now;
    }
    
    return {
      syncProgress: {
        ...progress,
        startTime,
        lastProcessedTime,
        processingTimes,
      },
    };
  }),
  clearSyncTiming: () => set((state) => ({
    syncProgress: {
      ...state.syncProgress,
      startTime: null,
      lastProcessedTime: null,
      processingTimes: [],
    },
  })),

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
