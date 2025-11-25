import { useState } from 'react';
import { open } from '@tauri-apps/plugin-dialog';
import { FolderOpen, Play } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { useAppStore } from '@/stores/appStore';
import { api } from '@/api/client';

export function FolderPicker() {
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [generateSummaries, setGenerateSummaries] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    setCurrentScan,
    setIsScanning,
    setScanProgress,
    setCurrentView,
    backendConnected,
  } = useAppStore();

  const handleSelectFolder = async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: 'Select folder to scan',
      });

      if (selected && typeof selected === 'string') {
        setSelectedPath(selected);
        setError(null);
      }
    } catch (err) {
      console.error('Failed to open folder dialog:', err);
      setError('Failed to open folder dialog');
    }
  };

  const handleStartScan = async () => {
    if (!selectedPath) return;

    setIsStarting(true);
    setError(null);

    try {
      const response = await api.scan.start({
        root_path: selectedPath,
        recursive: true,
        generate_summaries: generateSummaries,
      });

      setCurrentScan(response.scan_id, selectedPath);
      setIsScanning(true);
      setScanProgress({
        total: response.total_files,
        processed: response.processed_files,
        failed: response.failed_files,
      });
      setCurrentView('files');
    } catch (err) {
      console.error('Failed to start scan:', err);
      setError(err instanceof Error ? err.message : 'Failed to start scan');
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="flex h-full flex-col items-center justify-center p-8">
      <div className="w-full max-w-lg rounded-xl border border-border bg-bg-secondary p-8">
        <h2 className="mb-2 text-center text-2xl font-semibold text-text-primary">
          Select a Folder to Scan
        </h2>
        <p className="mb-8 text-center text-sm text-text-secondary">
          Choose a directory to analyze. FileVyasa will scan all files and
          generate AI-powered summaries.
        </p>

        <div
          onClick={handleSelectFolder}
          className="mb-6 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-bg-tertiary p-8 transition-colors hover:border-accent hover:bg-bg-hover"
        >
          <FolderOpen className="mb-3 h-12 w-12 text-text-muted" />
          {selectedPath ? (
            <div className="text-center">
              <p className="text-sm font-medium text-text-primary">
                Selected folder:
              </p>
              <p className="mt-1 max-w-md truncate text-sm text-accent">
                {selectedPath}
              </p>
            </div>
          ) : (
            <p className="text-sm text-text-secondary">
              Click to select a folder
            </p>
          )}
        </div>

        <div className="mb-6">
          <label className="flex items-center gap-3 text-sm text-text-secondary">
            <input
              type="checkbox"
              checked={generateSummaries}
              onChange={(e) => setGenerateSummaries(e.target.checked)}
              className="h-4 w-4 rounded border-border bg-bg-tertiary accent-accent"
            />
            Generate AI summaries for files
          </label>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-error/20 px-4 py-2 text-sm text-error">
            {error}
          </div>
        )}

        <Button
          onClick={handleStartScan}
          disabled={!selectedPath || isStarting || !backendConnected}
          className="w-full"
          size="lg"
        >
          <Play className="mr-2 h-5 w-5" />
          {isStarting ? 'Starting...' : 'Start Scan'}
        </Button>

        {!backendConnected && (
          <p className="mt-4 text-center text-sm text-warning">
            Backend is not connected. Please start the backend server first.
          </p>
        )}
      </div>
    </div>
  );
}
