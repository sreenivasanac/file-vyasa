import { useState, useRef, useLayoutEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { Save, Check, AlertCircle, Server, Cloud, FileText, FolderOpen, X, ShieldCheck, Cpu, Image } from 'lucide-react';
import { api } from '@/api/client';
import { Button } from '@/components/common/Button';
import { Spinner } from '@/components/common/Spinner';
import { Badge } from '@/components/common/Badge';

// Provider configurations with suggested models
// See https://docs.litellm.ai/docs/providers for full list
const PROVIDERS = {
  ollama: {
    name: 'Ollama',
    icon: Server,
    requiresApiKey: false,
    defaultApiBase: 'http://localhost:11434',
    models: ['llama3.2', 'llama3.1', 'llama3', 'mistral', 'mixtral', 'phi3', 'gemma2', 'qwen2.5', 'codellama'],
    description: 'Run models locally. No API key required.',
  },
  openai: {
    name: 'OpenAI',
    icon: Cloud,
    requiresApiKey: true,
    defaultApiBase: '',
    models: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo', 'o1-mini', 'o1-preview'],
    description: 'GPT models from OpenAI.',
  },
  anthropic: {
    name: 'Anthropic',
    icon: Cloud,
    requiresApiKey: true,
    defaultApiBase: '',
    models: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-haiku-20240307', 'claude-3-opus-20240229'],
    description: 'Claude models from Anthropic.',
  },
  gemini: {
    name: 'Gemini',
    icon: Cloud,
    requiresApiKey: true,
    defaultApiBase: '',
    models: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash', 'gemini-pro'],
    description: 'Google Gemini models.',
  },
  groq: {
    name: 'Groq',
    icon: Cloud,
    requiresApiKey: true,
    defaultApiBase: '',
    models: ['llama-3.1-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768', 'llama3-70b-8192'],
    description: 'Ultra-fast inference on Groq hardware.',
  },
  deepseek: {
    name: 'DeepSeek',
    icon: Cloud,
    requiresApiKey: true,
    defaultApiBase: '',
    models: ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'],
    description: 'Cost-effective models from DeepSeek.',
  },
  together_ai: {
    name: 'Together AI',
    icon: Cloud,
    requiresApiKey: true,
    defaultApiBase: '',
    models: ['meta-llama/Llama-3-70b-chat-hf', 'meta-llama/Llama-3-8b-chat-hf', 'mistralai/Mixtral-8x7B-Instruct-v0.1'],
    description: 'Wide variety of open-source models.',
  },
  fireworks_ai: {
    name: 'Fireworks',
    icon: Cloud,
    requiresApiKey: true,
    defaultApiBase: '',
    models: ['accounts/fireworks/models/llama-v3p1-70b-instruct', 'accounts/fireworks/models/mixtral-8x7b-instruct'],
    description: 'Fast inference with Fireworks AI.',
  },
};

type ProviderKey = keyof typeof PROVIDERS;

export function SettingsPanel() {
  const queryClient = useQueryClient();

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: api.config.get,
  });

  // Check llava model availability
  const { data: llavaStatus, isLoading: isCheckingLlava } = useQuery({
    queryKey: ['llava-status'],
    queryFn: api.config.checkLlavaStatus,
  });

  const [provider, setProvider] = useState<ProviderKey>('ollama');
  const [model, setModel] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiBase, setApiBase] = useState('');
  const [isSaved, setIsSaved] = useState(false);

  // Google credentials state
  const [googleCredentialsPath, setGoogleCredentialsPath] = useState('');
  const [isGoogleSaved, setIsGoogleSaved] = useState(false);
  const [verifyResult, setVerifyResult] = useState<{
    success: boolean;
    message: string;
    service_account_email?: string;
  } | null>(null);

  // Track if form has been initialized from config
  const isInitialized = useRef(false);

  // Initialize form with current config (only once when data arrives)
  const configProvider = config?.llm.provider as ProviderKey | undefined;
  const configModel = config?.llm.model;
  const configApiBase = config?.llm.api_base;

  // Use layout effect to set initial values before paint
  // This is a legitimate pattern for initializing form state from server data
  useLayoutEffect(() => {
    if (!isInitialized.current && config) {
      if (configProvider && PROVIDERS[configProvider]) {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setProvider(configProvider);
      }
      if (configModel) {
        setModel(configModel);
      }
      if (configApiBase !== undefined) {
        setApiBase(configApiBase || '');
      }
      if (config.google?.credentials_path) {
        setGoogleCredentialsPath(config.google.credentials_path);
      }
      isInitialized.current = true;
    }
  }, [config, configProvider, configModel, configApiBase]);

  const mutation = useMutation({
    mutationFn: api.config.updateLLM,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2000);
    },
  });

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

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" className="text-accent" />
      </div>
    );
  }

  const currentProviderConfig = PROVIDERS[provider];

  const handleProviderChange = (newProvider: ProviderKey) => {
    setProvider(newProvider);
    const providerConfig = PROVIDERS[newProvider];
    // Set default model for the new provider
    setModel(providerConfig.models[0]);
    setCustomModel('');
    // Set default API base
    setApiBase(providerConfig.defaultApiBase);
    // Clear API key when switching providers
    setApiKey('');
  };

  const handleSave = () => {
    const selectedModel = customModel || model;
    mutation.mutate({
      provider: provider,
      model: selectedModel,
      api_key: apiKey || undefined,
      api_base: apiBase || undefined,
    });
  };

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
    <div className="mx-auto max-w-2xl p-6">
      <h2 className="mb-6 text-xl font-semibold text-text-primary">Settings</h2>

      <section className="mb-8 rounded-lg border border-border bg-bg-secondary p-6">
        <h3 className="mb-4 font-medium text-text-primary">LLM Configuration</h3>
        <p className="mb-6 text-sm text-text-muted">
          Configure your AI provider for generating file summaries. Use Ollama for local
          processing or cloud providers with your own API key.
        </p>

        <div className="space-y-4">
          {/* Provider Selection */}
          <div>
            <label className="mb-2 block text-sm font-medium text-text-secondary">
              Provider
            </label>
            <div className="grid grid-cols-4 gap-2">
              {(Object.keys(PROVIDERS) as ProviderKey[]).map((key) => {
                const providerConfig = PROVIDERS[key];
                const Icon = providerConfig.icon;
                const isSelected = provider === key;
                return (
                  <button
                    key={key}
                    onClick={() => handleProviderChange(key)}
                    className={`flex flex-col items-center gap-1 rounded-lg border p-3 transition-colors ${
                      isSelected
                        ? 'border-accent bg-accent/10 text-accent'
                        : 'border-border bg-bg-tertiary text-text-secondary hover:border-accent/50'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="text-xs font-medium">{providerConfig.name}</span>
                  </button>
                );
              })}
            </div>
            <p className="mt-2 text-xs text-text-muted">
              {currentProviderConfig.description}
            </p>

            {/* Privacy Notice */}
            {provider === 'ollama' ? (
              <div className="mt-3 flex items-start gap-2 rounded-md border border-success/50 bg-success/10 p-3">
                <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-success" />
                <div className="text-xs">
                  <p className="font-medium text-success">Recommended for Privacy</p>
                  <p className="mt-1 text-text-muted">
                    Ollama runs entirely on your device. Your file contents never leave your computer,
                    ensuring complete privacy and data security.
                  </p>
                </div>
              </div>
            ) : (
              <div className="mt-3 flex items-start gap-2 rounded-md border border-warning/50 bg-warning/10 p-3">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-warning" />
                <div className="text-xs">
                  <p className="font-medium text-warning">Cloud Provider Notice</p>
                  <p className="mt-1 text-text-muted">
                    Your file contents will be sent to {currentProviderConfig.name}'s servers for processing.
                    If privacy is a concern, consider using Ollama which runs locally on your device.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Model Selection */}
          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              Model
            </label>
            <select
              value={model}
              onChange={(e) => {
                setModel(e.target.value);
                if (e.target.value !== 'custom') {
                  setCustomModel('');
                }
              }}
              className="w-full rounded-md border border-border bg-bg-tertiary px-3 py-2 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            >
              {currentProviderConfig.models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
              <option value="custom">Custom model...</option>
            </select>
            {model === 'custom' && (
              <input
                type="text"
                placeholder="Enter custom model name"
                value={customModel}
                onChange={(e) => setCustomModel(e.target.value)}
                className="mt-2 w-full rounded-md border border-border bg-bg-tertiary px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            )}
            <p className="mt-1 text-xs text-text-muted">
              Current: {config?.llm.model}
            </p>
          </div>

          {/* API Key - only show for providers that require it */}
          {currentProviderConfig.requiresApiKey && (
            <div>
              <label className="mb-1 block text-sm font-medium text-text-secondary">
                API Key
              </label>
              <input
                type="password"
                placeholder={provider === 'openai' ? 'sk-...' : 'Enter API key'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full rounded-md border border-border bg-bg-tertiary px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
              <div className="mt-1 flex items-center gap-2">
                {config?.llm.api_key_configured && config?.llm.provider === provider ? (
                  <Badge variant="success">
                    <Check className="mr-1 h-3 w-3" />
                    Configured
                  </Badge>
                ) : (
                  <Badge variant="warning">
                    <AlertCircle className="mr-1 h-3 w-3" />
                    Required
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* Ollama Status */}
          {provider === 'ollama' && (
            <div className="rounded-md border border-border bg-bg-tertiary p-3">
              <div className="flex items-center gap-2 text-sm">
                <Server className="h-4 w-4 text-accent" />
                <span className="text-text-secondary">
                  Make sure Ollama is running locally at{' '}
                  <code className="rounded bg-bg-primary px-1 py-0.5 text-xs">
                    {apiBase || 'http://localhost:11434'}
                  </code>
                </span>
              </div>
              <p className="mt-1 text-xs text-text-muted">
                Install Ollama from{' '}
                <a
                  href="https://ollama.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent hover:underline"
                >
                  ollama.ai
                </a>
                {' '}and run <code className="rounded bg-bg-primary px-1 py-0.5 text-xs">ollama pull {model}</code>
              </p>
            </div>
          )}

          {/* API Base URL */}
          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              API Base URL
            </label>
            <input
              type="text"
              placeholder={currentProviderConfig.defaultApiBase || 'Default'}
              value={apiBase}
              onChange={(e) => setApiBase(e.target.value)}
              className="w-full rounded-md border border-border bg-bg-tertiary px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
            {config?.llm.api_base && (
              <p className="mt-1 text-xs text-text-muted">
                Current: {config.llm.api_base}
              </p>
            )}
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Button onClick={handleSave} disabled={mutation.isPending}>
              <Save className="mr-2 h-4 w-4" />
              {mutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
            {isSaved && (
              <span className="text-sm text-success">
                <Check className="mr-1 inline h-4 w-4" />
                Saved successfully
              </span>
            )}
            {mutation.isError && (
              <span className="text-sm text-error">
                Failed to save settings
              </span>
            )}
          </div>
        </div>
      </section>

      <section className="mb-8 rounded-lg border border-border bg-bg-secondary p-6">
        <h3 className="mb-4 font-medium text-text-primary">Google Workspace Integration</h3>
        <p className="mb-6 text-sm text-text-muted">
          Configure access to Google Docs, Sheets, Slides, Forms, and Drawings files.
          Requires a Google Cloud service account with appropriate API access.
        </p>

        <div className="space-y-4">
          {/* Credentials File Selection */}
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

          {/* Status Badge */}
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

          {/* Help Text */}
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
              <li>Navigate to <strong className="text-text-secondary">IAM & Admin</strong> → <strong className="text-text-secondary">Service Accounts</strong></li>
              <li>Click <strong className="text-text-secondary">+ Create Service Account</strong>, give it a name</li>
              <li>Click <strong className="text-text-secondary">Create and Continue</strong> (skip optional permissions), then <strong className="text-text-secondary">Done</strong></li>
              <li>Click on the newly created service account</li>
              <li>Go to <strong className="text-text-secondary">Keys</strong> tab → <strong className="text-text-secondary">Add Key</strong> → <strong className="text-text-secondary">Create new key</strong> → <strong className="text-text-secondary">JSON</strong></li>
              <li>Download the JSON file and select it above</li>
            </ol>
            <p className="mt-2 text-xs text-warning">
              <strong>Important:</strong> You may sometimes need to share Google Docs/Sheets with the service account email
              (e.g., <code className="rounded bg-bg-primary px-1 py-0.5 text-xs">name@project-id.iam.gserviceaccount.com</code>)
              for access.
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
              <span className="text-sm text-error">
                Failed to save credentials
              </span>
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

      <section className="mb-8 rounded-lg border border-border bg-bg-secondary p-6">
        <div className="mb-4 flex items-center gap-2">
          <Image className="h-5 w-5 text-accent" />
          <h3 className="font-medium text-text-primary">Image Description Model</h3>
        </div>
        <p className="mb-4 text-sm text-text-muted">
          Image descriptions use <strong className="text-text-secondary">Ollama llava</strong> model exclusively.
          This runs locally on your device for privacy.
        </p>

        {/* Status Indicator */}
        <div className={`mb-4 rounded-md border p-3 ${
          isCheckingLlava
            ? 'border-border bg-bg-tertiary'
            : llavaStatus?.available
              ? 'border-success/50 bg-success/10'
              : 'border-warning/50 bg-warning/10'
        }`}>
          <div className="flex items-center gap-2">
            {isCheckingLlava ? (
              <>
                <Cpu className="h-4 w-4 animate-pulse text-text-muted" />
                <span className="text-sm text-text-muted">Checking Ollama llava model...</span>
              </>
            ) : llavaStatus?.available ? (
              <>
                <Check className="h-4 w-4 text-success" />
                <span className="text-sm text-success">llava model is running</span>
                <Badge variant="success" className="ml-auto">Ready</Badge>
              </>
            ) : (
              <>
                <AlertCircle className="h-4 w-4 text-warning" />
                <span className="text-sm text-warning">llava model not available</span>
                <Badge variant="warning" className="ml-auto">Not Ready</Badge>
              </>
            )}
          </div>
        </div>

        {/* Install Instructions */}
        <div className="rounded-md border border-border bg-bg-tertiary p-3">
          <div className="flex items-center gap-2 text-sm">
            <Cpu className="h-4 w-4 text-accent" />
            <span className="text-text-secondary">Setup Instructions</span>
          </div>
          <ol className="mt-2 list-inside list-decimal space-y-1 text-xs text-text-muted">
            <li>
              Install Ollama from{' '}
              <a
                href="https://ollama.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:underline"
              >
                ollama.ai
              </a>
            </li>
            <li>
              Run: <code className="rounded bg-bg-primary px-1 py-0.5 text-xs">ollama pull llava</code>
            </li>
            <li>Ensure Ollama is running when using image descriptions</li>
          </ol>
        </div>

        {/* Privacy Notice */}
        <div className="mt-3 flex items-start gap-2 rounded-md border border-success/50 bg-success/10 p-3">
          <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-success" />
          <div className="text-xs">
            <p className="font-medium text-success">Privacy Protected</p>
            <p className="mt-1 text-text-muted">
              Image analysis runs entirely on your device. Your images never leave your computer.
            </p>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-border bg-bg-secondary p-6">
        <h3 className="mb-4 font-medium text-text-primary">App Information</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-text-muted">App Name</span>
            <span className="text-text-secondary">{config?.app_name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Version</span>
            <span className="text-text-secondary">{config?.version}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Database Path</span>
            <span className="text-text-secondary">{config?.db_path}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Max Content Lines</span>
            <span className="text-text-secondary">
              {config?.max_content_lines}
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
