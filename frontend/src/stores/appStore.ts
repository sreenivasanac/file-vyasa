import { create } from 'zustand';
import type { FileObject, ScanResponse } from '@/types';

type View = 'scan' | 'files' | 'recent' | 'settings';

interface AppState {
  // Navigation
  currentView: View;
  setCurrentView: (view: View) => void;

  // Scan state
  currentScanId: string | null;
  currentScanPath: string | null;
  isScanning: boolean;
  scanProgress: {
    total: number;
    processed: number;
    failed: number;
  };
  setCurrentScan: (scanId: string | null, path: string | null) => void;
  setIsScanning: (isScanning: boolean) => void;
  setScanProgress: (progress: { total: number; processed: number; failed: number }) => void;

  // Files state
  selectedFileId: string | null;
  setSelectedFileId: (fileId: string | null) => void;
  selectedFile: FileObject | null;
  setSelectedFile: (file: FileObject | null) => void;

  // Recent scans
  recentScans: ScanResponse[];
  setRecentScans: (scans: ScanResponse[]) => void;

  // Backend status
  backendConnected: boolean;
  setBackendConnected: (connected: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Navigation
  currentView: 'scan',
  setCurrentView: (view) => set({ currentView: view }),

  // Scan state
  currentScanId: null,
  currentScanPath: null,
  isScanning: false,
  scanProgress: { total: 0, processed: 0, failed: 0 },
  setCurrentScan: (scanId, path) =>
    set({ currentScanId: scanId, currentScanPath: path }),
  setIsScanning: (isScanning) => set({ isScanning }),
  setScanProgress: (progress) => set({ scanProgress: progress }),

  // Files state
  selectedFileId: null,
  setSelectedFileId: (fileId) => set({ selectedFileId: fileId }),
  selectedFile: null,
  setSelectedFile: (file) => set({ selectedFile: file }),

  // Recent scans
  recentScans: [],
  setRecentScans: (scans) => set({ recentScans: scans }),

  // Backend status
  backendConnected: false,
  setBackendConnected: (connected) => set({ backendConnected: connected }),
}));
