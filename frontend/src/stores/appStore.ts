import { create } from 'zustand';
import type { FileObject, MonitoredFolder } from '@/types';
import {
  type SyncProgressData,
  updateSyncProgress,
  INITIAL_SYNC_PROGRESS,
} from '@/lib/syncUtils';

export type View = 'add-folder' | 'folders' | 'files' | 'settings';

export type SettingsSection = 'overview' | 'general' | 'ai' | 'integrations';

interface AppState {
  // App config
  appName: string;
  setAppName: (name: string) => void;

  // Navigation
  currentView: View;
  setCurrentView: (view: View) => void;

  // Settings navigation
  settingsSection: SettingsSection;
  settingsContext: {
    origin?: string;
    highlight?: string;
  } | null;
  setSettingsSection: (section: SettingsSection, context?: { origin?: string; highlight?: string }) => void;
  clearSettingsContext: () => void;

  // Folder state
  currentFolderId: string | null;
  currentFolderPath: string | null;
  isSyncing: boolean;
  syncProgress: SyncProgressData;
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
  addFolder: (folder: MonitoredFolder) => void;
  updateFolder: (folder: MonitoredFolder) => void;

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

  // Settings navigation
  settingsSection: 'overview',
  settingsContext: null,
  setSettingsSection: (section, context) =>
    set({ settingsSection: section, settingsContext: context ?? null }),
  clearSettingsContext: () => set({ settingsContext: null }),

  // Folder state
  currentFolderId: null,
  currentFolderPath: null,
  isSyncing: false,
  syncProgress: INITIAL_SYNC_PROGRESS,
  setCurrentFolder: (folderId, path) =>
    set({ currentFolderId: folderId, currentFolderPath: path }),
  setIsSyncing: (isSyncing) => set({ isSyncing }),
  setSyncProgress: (progress) =>
    set((state) => ({
      syncProgress: updateSyncProgress(state.syncProgress, progress),
    })),
  clearSyncTiming: () =>
    set((state) => ({
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
  addFolder: (folder) => set((state) => ({ folders: [folder, ...state.folders] })),
  updateFolder: (folder) =>
    set((state) => ({
      folders: state.folders.map((f) => (f.id === folder.id ? { ...f, ...folder } : f)),
    })),

  // Backend status
  backendConnected: false,
  setBackendConnected: (connected) => set({ backendConnected: connected }),
}));
