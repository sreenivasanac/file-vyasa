import { useState, useRef, useLayoutEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { Save, Check, AlertCircle, FileText, FolderOpen, X, ShieldCheck } from 'lucide-react';
import { api } from '@/api/client';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { cn } from '@/lib/utils';
import type { AppConfig } from '@/types';

interface SettingsIntegrationsTabProps {
  config: AppConfig | undefined;
  highlightGoogle: boolean;
}

export function SettingsIntegrationsTab({ config, highlightGoogle }: SettingsIntegrationsTabProps) {
  const queryClient = useQueryClient();

  const [googleCredentialsPath, setGoogleCredentialsPath] = useState('');
  const [isGoogleSaved, setIsGoogleSaved] = useState(false);
  const [verifyResult, setVerifyResult] = useState<{
    success: boolean;
    message: string;
    service_account_email?: string;
  } | null>(null);

  const isInitialized = useRef(false);

  useLayoutEffect(() => {
    if (!isInitialized.current && config?.google?.credentials_path) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setGoogleCredentialsPath(config.google.credentials_path);
      isInitialized.current = true;
    }
  }, [config]);

  const googleMutation = useMutation({
    mutationFn: api.config.updateGoogle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setIsGoogleSaved(true);
      setTimeout(() => setIsGoogleSaved(false), 2000);
    },
  });

  const verifyGoogleMutation = useMutation({
    mutationFn: api.config.verifyGoogle,
    onSuccess: (data) => {
      setVerifyResult(data);
    },
    onError: (error) => {
      setVerifyResult({
        success: false,
        message: `Verification failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    },
  });

  const handleSelectGoogleCredentials = async () => {
    try {
      const selected = await open({
        multiple: false,
        title: 'Select Google Service Account Credentials JSON',
        filters: [{ name: 'JSON', extensions: ['json'] }],
      });

      if (selected && typeof selected === 'string') {
        setGoogleCredentialsPath(selected);
      }
    } catch (err) {
      console.error('Failed to open file dialog:', err);
    }
  };

  const handleClearGoogleCredentials = () => {
    setGoogleCredentialsPath('');
  };

  const handleSaveGoogleCredentials = () => {
    googleMutation.mutate({
      credentials_path: googleCredentialsPath || undefined,
    });
  };

  const handleVerifyGoogleCredentials = () => {
    setVerifyResult(null);
    verifyGoogleMutation.mutate();
  };

  return (
    <section
      className={cn(
        'rounded-lg border border-border bg-bg-secondary p-6',
        highlightGoogle && 'border-accent ring-1 ring-accent/60',
      )}
    >
      <h3 className="mb-4 font-medium text-text-primary">Google Workspace Integration</h3>
      <p className="mb-6 text-sm text-text-muted">
        Configure access to Google Docs, Sheets, Slides, Forms, and Drawings files. Requires a
        Google Cloud service account with appropriate API access.
      </p>

      <div className="space-y-4">
        <div>
          <label className="mb-2 block text-sm font-medium text-text-secondary">
            Service Account Credentials
          </label>
          <div className="flex items-center gap-2">
            <div
              onClick={handleSelectGoogleCredentials}
              className="flex flex-1 cursor-pointer items-center gap-2 rounded-md border border-border bg-bg-tertiary px-3 py-2 text-sm transition-colors hover:border-accent/50"
            >
              <FolderOpen className="h-4 w-4 text-text-muted" />
              {googleCredentialsPath ? (
                <span className="truncate text-text-primary">
                  {googleCredentialsPath.split('/').pop()}
                </span>
              ) : (
                <span className="text-text-muted">Select credentials.json file...</span>
              )}
            </div>
            {googleCredentialsPath && (
              <button
                onClick={handleClearGoogleCredentials}
                className="rounded-md p-2 text-text-muted hover:bg-bg-tertiary hover:text-error"
                title="Clear credentials"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          {googleCredentialsPath && (
            <p className="mt-1 truncate text-xs text-text-muted" title={googleCredentialsPath}>
              Path: {googleCredentialsPath}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            {config?.google?.credentials_configured ? (
              <Badge variant="success">
                <Check className="mr-1 h-3 w-3" />
                Configured
              </Badge>
            ) : (
              <Badge variant="default">
                <FileText className="mr-1 h-3 w-3" />
                Not configured
              </Badge>
            )}
          </div>
          {config?.google?.credentials_path && (
            <div className="rounded-md border border-success/30 bg-success/5 p-2">
              <p className="text-xs text-text-muted">
                <span className="font-medium text-text-secondary">Saved credentials file:</span>
              </p>
              <p className="mt-1 break-all text-xs text-success" title={config.google.credentials_path}>
                {config.google.credentials_path}
              </p>
            </div>
          )}
        </div>

        <div className="rounded-md border border-border bg-bg-tertiary p-3">
          <p className="text-xs text-text-muted">
            <strong className="text-text-secondary">Setup instructions:</strong>{' '}
            <a
              href="https://developers.google.com/workspace/guides/get-started"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              Getting Started Guide
            </a>
          </p>
          <ol className="mt-2 list-inside list-decimal space-y-1 text-xs text-text-muted">
            <li>
              Go to{' '}
              <a
                href="https://console.cloud.google.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:underline"
              >
                Google Cloud Console
              </a>
              {' '}and create a project
            </li>
            <li>
              <a
                href="https://developers.google.com/workspace/guides/enable-apis"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:underline"
              >
                Enable Workspace APIs
              </a>
              {' '}(Drive, Docs, Sheets, Slides, Forms)
            </li>
            <li>
              Navigate to <strong className="text-text-secondary">IAM &amp; Admin</strong> →{' '}
              <strong className="text-text-secondary">Service Accounts</strong>
            </li>
            <li>
              Click <strong className="text-text-secondary">+ Create Service Account</strong>, give it a
              name
            </li>
            <li>
              Click <strong className="text-text-secondary">Create and Continue</strong> (skip optional
              permissions), then <strong className="text-text-secondary">Done</strong>
            </li>
            <li>Click on the newly created service account</li>
            <li>
              Go to <strong className="text-text-secondary">Keys</strong> tab →{' '}
              <strong className="text-text-secondary">Add Key</strong> →{' '}
              <strong className="text-text-secondary">Create new key</strong> →{' '}
              <strong className="text-text-secondary">JSON</strong>
            </li>
            <li>Download the JSON file and select it above</li>
          </ol>
          <p className="mt-2 text-xs text-warning">
            <strong>Important:</strong> You may sometimes need to share Google Docs/Sheets with the
            service account email (e.g.,
            {' '}
            <code className="rounded bg-bg-primary px-1 py-0.5 text-xs">
              name@project-id.iam.gserviceaccount.com
            </code>
            ) for access.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <Button onClick={handleSaveGoogleCredentials} disabled={googleMutation.isPending}>
            <Save className="mr-2 h-4 w-4" />
            {googleMutation.isPending ? 'Saving...' : 'Save Credentials'}
          </Button>
          <Button
            onClick={handleVerifyGoogleCredentials}
            disabled={verifyGoogleMutation.isPending || !config?.google?.credentials_configured}
            variant="secondary"
          >
            <ShieldCheck className="mr-2 h-4 w-4" />
            {verifyGoogleMutation.isPending ? 'Verifying...' : 'Verify Auth'}
          </Button>
          {isGoogleSaved && (
            <span className="text-sm text-success">
              <Check className="mr-1 inline h-4 w-4" />
              Saved successfully
            </span>
          )}
          {googleMutation.isError && (
            <span className="text-sm text-error">Failed to save credentials</span>
          )}
        </div>

        {verifyResult && (
          <div
            className={`mt-3 rounded-md border p-3 ${
              verifyResult.success
                ? 'border-success/50 bg-success/10'
                : 'border-error/50 bg-error/10'
            }`}
          >
            <p
              className={`text-sm ${
                verifyResult.success ? 'text-success' : 'text-error'
              }`}
            >
              {verifyResult.success ? (
                <Check className="mr-1 inline h-4 w-4" />
              ) : (
                <AlertCircle className="mr-1 inline h-4 w-4" />
              )}
              {verifyResult.message}
            </p>
            {verifyResult.service_account_email && (
              <p className="mt-1 text-xs text-text-muted">
                Service Account: {verifyResult.service_account_email}
              </p>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
