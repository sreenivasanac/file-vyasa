import { useState } from 'react';
import { Cpu, Check, AlertCircle, Cloud, ShieldCheck, Settings } from 'lucide-react';

import { api } from '@/api/client';
import type { AppConfig } from '@/types';

interface LlavaStatus {
  available: boolean;
}

interface AddFolderOptionsProps {
  generateDocumentSummaries: boolean;
  onGenerateDocumentSummariesChange: (value: boolean) => void;
  generateImageDescriptions: boolean;
  onGenerateImageDescriptionsChange: (value: boolean) => void;
  extractMediaTranscriptions: boolean;
  onExtractMediaTranscriptionsChange: (value: boolean) => void;
  config: AppConfig | undefined;
  llavaStatus: LlavaStatus | undefined;
  isCheckingLlava: boolean;
  onOpenAiSettings: () => void;
  onOpenGoogleWorkspaceSettings: () => void;
}

export function AddFolderOptions({
  generateDocumentSummaries,
  onGenerateDocumentSummariesChange,
  generateImageDescriptions,
  onGenerateImageDescriptionsChange,
  extractMediaTranscriptions,
  onExtractMediaTranscriptionsChange,
  config,
  llavaStatus,
  isCheckingLlava,
  onOpenAiSettings,
  onOpenGoogleWorkspaceSettings,
}: AddFolderOptionsProps) {
  const [isVerifyingGoogle, setIsVerifyingGoogle] = useState(false);
  const [googleVerifyResult, setGoogleVerifyResult] = useState<
    | {
        success: boolean;
        message: string;
        service_account_email?: string;
      }
    | null
  >(null);

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

  return (
    <div className="mb-6 space-y-4">
      <p className="text-sm font-medium text-text-primary">AI Processing Options:</p>

      {/* Document Summaries */}
      <div className="rounded-lg border border-border/50 bg-bg-tertiary/30 p-3">
        <label className="flex items-center gap-3 text-sm text-text-secondary">
          <input
            type="checkbox"
            checked={generateDocumentSummaries}
            onChange={(e) => onGenerateDocumentSummariesChange(e.target.checked)}
            className="h-4 w-4 rounded border-border bg-bg-tertiary accent-accent"
          />
          <span className="text-text-primary">Generate AI summaries for Documents</span>
          <span className="text-xs text-text-muted">(PDF, DOCX, TXT, etc.)</span>
        </label>
        {generateDocumentSummaries && config && (
          <div className="ml-7 mt-2 flex items-center gap-2 text-xs text-text-muted">
            <Cpu className="h-3 w-3" />
            <span>
              Using:{' '}
              <span className="text-text-secondary">
                {config.llm.provider}/{config.llm.model}
              </span>
            </span>
            <button
              onClick={onOpenAiSettings}
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
            onChange={(e) => onGenerateImageDescriptionsChange(e.target.checked)}
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
              <AlertCircle className="h-3 w-3" /> Requires local Ollama llava - run:{' '}
              <code className="ml-1 rounded bg-bg-tertiary px-1">ollama pull llava</code>
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
            onChange={(e) => onExtractMediaTranscriptionsChange(e.target.checked)}
            className="h-4 w-4 rounded border-border bg-bg-tertiary accent-accent"
          />
          <span className="text-text-primary">Extract audio transcription for Media files</span>
        </label>
        {extractMediaTranscriptions && (
          <div className="ml-7 mt-2 flex items-center gap-1 text-xs text-text-muted">
            <Cpu className="h-3 w-3" />
            <span>
              Uses local <span className="text-text-secondary">OpenAI Whisper</span> model (runs on
              device)
            </span>
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
                <div
                  className={`text-xs ${
                    googleVerifyResult.success ? 'text-success' : 'text-error'
                  }`}
                >
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
                <AlertCircle className="h-3 w-3" /> Not configured - .gdoc/.gsheet files will show
                basic info only
              </span>
              <button
                onClick={onOpenGoogleWorkspaceSettings}
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
  );
}
