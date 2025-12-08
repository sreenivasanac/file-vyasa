import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { FolderOpen, Plus } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { BackendDisconnected } from '@/components/common/BackendDisconnected';
import { useAppStore } from '@/stores/appStore';
import { api } from '@/api/client';
import { AddFolderOptions } from './AddFolderOptions';

export function AddFolder() {
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  // AI processing options - all enabled by default
  const [generateDocumentSummaries, setGenerateDocumentSummaries] = useState(true);
  const [generateImageDescriptions, setGenerateImageDescriptions] = useState(true);
  const [extractMediaTranscriptions, setExtractMediaTranscriptions] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const {
    setCurrentFolder,
    setIsSyncing,
    setSyncProgress,
    setCurrentView,
    setSettingsSection,
    backendConnected,
    addFolder,
  } = useAppStore();

  // Fetch current LLM config
  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: api.config.get,
  });

  // Check llava availability when image descriptions is enabled
  const { data: llavaStatus, isLoading: isCheckingLlava } = useQuery({
    queryKey: ['llava-status'],
    queryFn: api.config.checkLlavaStatus,
    enabled: generateImageDescriptions,
  });

  // Determine if Add Folder button should be disabled
  const canAddFolder = () => {
    if (!selectedPath) return false;
    if (generateImageDescriptions && llavaStatus && !llavaStatus.available) return false;
    return true;
  };

  // Show disconnected state when backend is not available
  if (!backendConnected) {
    return <BackendDisconnected />;
  }

  const handleSelectFolder = async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: 'Select folder to monitor',
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

  const handleAddFolder = async () => {
    if (!selectedPath) return;

    setIsAdding(true);
    setError(null);

    try {
      const folder = await api.folders.add({
        root_path: selectedPath,
        generate_document_summaries: generateDocumentSummaries,
        generate_image_descriptions: generateImageDescriptions,
        extract_media_transcriptions: extractMediaTranscriptions,
      });

      // Add folder to store immediately so FileList can display it
      addFolder(folder);

      // Folder is auto-syncing after add
      setCurrentFolder(folder.id, folder.root_path);
      setIsSyncing(true);
      setSyncProgress({
        total: folder.total_files,
        processed: folder.processed_files,
        failed: folder.failed_files,
      });

      // Invalidate folders list (will refresh in background)
      queryClient.invalidateQueries({ queryKey: ['folders'] });

      // Navigate to files view
      setCurrentView('files');
    } catch (err) {
      console.error('Failed to add folder:', err);
      // Parse error message from API
      let errorMessage = 'Failed to add folder';
      if (err instanceof Error) {
        try {
          const parsed = JSON.parse(err.message);
          errorMessage = parsed.detail || err.message;
        } catch {
          errorMessage = err.message;
        }
      }
      setError(errorMessage);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="flex h-full flex-col items-center justify-center p-8">
      <div className="w-full max-w-lg rounded-xl border border-border bg-bg-secondary p-8">
        <h2 className="mb-2 text-center text-2xl font-semibold text-text-primary">
          Add a Folder to Monitor
        </h2>
        <p className="mb-8 text-center text-sm text-text-secondary">
          Choose a directory to monitor. FileVyasa will scan all files and
          generate AI-powered summaries. You can sync anytime to detect changes.
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
        <AddFolderOptions
          generateDocumentSummaries={generateDocumentSummaries}
          onGenerateDocumentSummariesChange={setGenerateDocumentSummaries}
          generateImageDescriptions={generateImageDescriptions}
          onGenerateImageDescriptionsChange={setGenerateImageDescriptions}
          extractMediaTranscriptions={extractMediaTranscriptions}
          onExtractMediaTranscriptionsChange={setExtractMediaTranscriptions}
          config={config}
          llavaStatus={llavaStatus}
          isCheckingLlava={isCheckingLlava}
          onOpenAiSettings={() => {
            setSettingsSection('ai', { origin: 'add-folder', highlight: 'llm' });
            setCurrentView('settings');
          }}
          onOpenGoogleWorkspaceSettings={() => {
            setSettingsSection('integrations', {
              origin: 'add-folder',
              highlight: 'google-workspace',
            });
            setCurrentView('settings');
          }}
        />

        {error && (
          <div className="mb-4 rounded-md bg-error/20 px-4 py-2 text-sm text-error">
            {error}
          </div>
        )}

        <Button
          onClick={handleAddFolder}
          disabled={!canAddFolder() || isAdding}
          className="w-full"
          size="lg"
        >
          <Plus className="mr-2 h-5 w-5" />
          {isAdding ? 'Adding...' : 'Add Folder'}
        </Button>
      </div>
    </div>
  );
}
