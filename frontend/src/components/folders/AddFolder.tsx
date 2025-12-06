import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { FolderOpen, Plus, Settings, Cpu, Check, AlertCircle, Cloud, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { useAppStore } from '@/stores/appStore';
import { api } from '@/api/client';

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

  // Google Workspace verification state
  const [isVerifyingGoogle, setIsVerifyingGoogle] = useState(false);
  const [googleVerifyResult, setGoogleVerifyResult] = useState<{
    success: boolean;
    message: string;
    service_account_email?: string;
  } | null>(null);

  const handleVerifyGoogle = async () => {
    setIsVerifyingGoogle(true);
    setGoogleVerifyResult(null);
    try {
      const result = await api.config.verifyGoogle();
      setGoogleVerifyResult(result);
    } catch (err) {
      setGoogleVerifyResult({
        success: false,
        message: err instanceof Error ? err.message : 'Verification failed',
      });
    } finally {
      setIsVerifyingGoogle(false);
    }
  };

  // Determine if Add Folder button should be disabled
  const canAddFolder = () => {
    if (!selectedPath || !backendConnected) return false;
    if (generateImageDescriptions && llavaStatus && !llavaStatus.available) return false;
    return true;
  };

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

        <div className="mb-6 space-y-4">
          <p className="text-sm font-medium text-text-primary">AI Processing Options:</p>
          
          {/* Document Summaries */}
          <div className="rounded-lg border border-border/50 bg-bg-tertiary/30 p-3">
            <label className="flex items-center gap-3 text-sm text-text-secondary">
              <input
                type="checkbox"
                checked={generateDocumentSummaries}
                onChange={(e) => setGenerateDocumentSummaries(e.target.checked)}
                className="h-4 w-4 rounded border-border bg-bg-tertiary accent-accent"
              />
              <span className="text-text-primary">Generate AI summaries for Documents</span>
              <span className="text-xs text-text-muted">(PDF, DOCX, TXT, etc.)</span>
            </label>
            {generateDocumentSummaries && config && (
              <div className="ml-7 mt-2 flex items-center gap-2 text-xs text-text-muted">
                <Cpu className="h-3 w-3" />
                <span>
                  Using: <span className="text-text-secondary">{config.llm.provider}/{config.llm.model}</span>
                </span>
                <button
                  onClick={() => setCurrentView('settings')}
                  className="ml-1 flex items-center gap-1 text-accent hover:underline"
                >
                  <Settings className="h-3 w-3" />
                  Change
                </button>
              </div>
            )}
          </div>
          
          {/* Image Descriptions */}
          <div className="rounded-lg border border-border/50 bg-bg-tertiary/30 p-3">
            <label className="flex items-center gap-3 text-sm text-text-secondary">
              <input
                type="checkbox"
                checked={generateImageDescriptions}
                onChange={(e) => setGenerateImageDescriptions(e.target.checked)}
                className="h-4 w-4 rounded border-border bg-bg-tertiary accent-accent"
              />
              <span className="text-text-primary">Generate AI descriptions for Images</span>
            </label>
            <div className="ml-7 mt-2">
              {isCheckingLlava ? (
                <span className="flex items-center gap-1 text-xs text-text-muted">
                  <Cpu className="h-3 w-3 animate-pulse" /> Checking Ollama llava model...
                </span>
              ) : llavaStatus?.available ? (
                <span className="flex items-center gap-1 text-xs text-success">
                  <Check className="h-3 w-3" /> Uses local Ollama llava model (running)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-error">
                  <AlertCircle className="h-3 w-3" /> Requires local Ollama llava - run: <code className="ml-1 rounded bg-bg-tertiary px-1">ollama pull llava</code>
                </span>
              )}
            </div>
          </div>
          
          {/* Media Transcription */}
          <div className="rounded-lg border border-border/50 bg-bg-tertiary/30 p-3">
            <label className="flex items-center gap-3 text-sm text-text-secondary">
              <input
                type="checkbox"
                checked={extractMediaTranscriptions}
                onChange={(e) => setExtractMediaTranscriptions(e.target.checked)}
                className="h-4 w-4 rounded border-border bg-bg-tertiary accent-accent"
              />
              <span className="text-text-primary">Extract audio transcription for Media files</span>
            </label>
            {extractMediaTranscriptions && (
              <div className="ml-7 mt-2 flex items-center gap-1 text-xs text-text-muted">
                <Cpu className="h-3 w-3" />
                <span>Uses local <span className="text-text-secondary">OpenAI Whisper</span> model (runs on device)</span>
              </div>
            )}
          </div>

          {/* Google Workspace */}
          <div className="rounded-lg border border-border/50 bg-bg-tertiary/30 p-3">
            <div className="flex items-center gap-3 text-sm">
              <Cloud className="h-4 w-4 text-accent" />
              <span className="text-text-primary">Google Drive / Workspace Files</span>
              <span className="text-xs text-text-muted">(Docs, Sheets, Slides, Forms)</span>
            </div>
            <div className="ml-7 mt-2">
              {config?.google?.credentials_configured ? (
                <div className="space-y-2">
                  <span className="flex items-center gap-1 text-xs text-success">
                    <Check className="h-3 w-3" /> Credentials configured
                  </span>
                  {!googleVerifyResult && (
                    <button
                      onClick={handleVerifyGoogle}
                      disabled={isVerifyingGoogle}
                      className="flex items-center gap-1 text-xs text-accent hover:underline"
                    >
                      <ShieldCheck className="h-3 w-3" />
                      {isVerifyingGoogle ? 'Verifying...' : 'Verify connection'}
                    </button>
                  )}
                  {googleVerifyResult && (
                    <div className={`text-xs ${googleVerifyResult.success ? 'text-success' : 'text-error'}`}>
                      {googleVerifyResult.success ? (
                        <span className="flex items-center gap-1">
                          <Check className="h-3 w-3" />
                          Connected as {googleVerifyResult.service_account_email}
                        </span>
                      ) : (
                        <span className="flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {googleVerifyResult.message}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-1">
                  <span className="flex items-center gap-1 text-xs text-text-muted">
                    <AlertCircle className="h-3 w-3" /> Not configured - .gdoc/.gsheet files will show basic info only
                  </span>
                  <button
                    onClick={() => setCurrentView('settings')}
                    className="flex items-center gap-1 text-xs text-accent hover:underline"
                  >
                    <Settings className="h-3 w-3" />
                    Configure in Settings
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

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

        {!backendConnected && (
          <p className="mt-4 text-center text-sm text-warning">
            Backend is not connected. Please start the backend server first.
          </p>
        )}
      </div>
    </div>
  );
}
