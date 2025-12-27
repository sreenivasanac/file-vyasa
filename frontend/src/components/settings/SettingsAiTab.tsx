import { useState, useRef, useLayoutEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, Check, AlertCircle, Server, Cloud, ShieldCheck, Cpu, Image, Globe } from 'lucide-react';
import { api } from '@/api/client';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { cn } from '@/lib/utils';
import type { AppConfig } from '@/types';

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
  ollama_cloud: {
    name: 'Ollama Cloud',
    icon: Globe,
    requiresApiKey: true,
    defaultApiBase: 'https://ollama.com/v1',
    models: ['gpt-oss:120b', 'gpt-oss:20b', 'qwen3:8b', 'qwen3:4b', 'llama3.1:70b', 'gemma3:27b', 'deepseek-r1:70b'],
    description: 'Powerful cloud models hosted by Ollama on high-end GPU servers.',
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
} as const;

export type ProviderKey = keyof typeof PROVIDERS;

interface SettingsAiTabProps {
  config: AppConfig | undefined;
  highlightLlm: boolean;
}

export function SettingsAiTab({ config, highlightLlm }: SettingsAiTabProps) {
  const queryClient = useQueryClient();

  const [provider, setProvider] = useState<ProviderKey>('ollama');
  const [model, setModel] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiBase, setApiBase] = useState('');
  const [isSaved, setIsSaved] = useState(false);

  // Track if form has been initialized from config
  const isInitialized = useRef(false);

  const configProvider = config?.llm?.provider as ProviderKey | undefined;
  const configModel = config?.llm?.model as string | undefined;
  const configApiBase = config?.llm?.api_base as string | undefined;

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
      isInitialized.current = true;
    }
  }, [config, configProvider, configModel, configApiBase]);

  const { data: llavaStatus, isLoading: isCheckingLlava } = useQuery({
    queryKey: ['llava-status'],
    queryFn: api.config.checkLlavaStatus,
  });

  const mutation = useMutation({
    mutationFn: api.config.updateLLM,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2000);
    },
  });

  const currentProviderConfig = PROVIDERS[provider];

  const handleProviderChange = (newProvider: ProviderKey) => {
    setProvider(newProvider);
    const providerConfig = PROVIDERS[newProvider];
    setModel(providerConfig.models[0]);
    setCustomModel('');
    setApiBase(providerConfig.defaultApiBase);
    setApiKey('');
  };

  const handleSave = () => {
    const selectedModel = customModel || model;
    mutation.mutate({
      provider,
      model: selectedModel,
      api_key: apiKey || undefined,
      api_base: apiBase || undefined,
    });
  };

  return (
    <>
      <section
        className={cn(
          'rounded-lg border border-border bg-bg-secondary p-6',
          highlightLlm && 'border-accent ring-1 ring-accent/60',
        )}
      >
        <h3 className="mb-4 font-medium text-text-primary">LLM Configuration</h3>
        <p className="mb-6 text-sm text-text-muted">
          Configure your AI provider for generating file summaries. Use Ollama for local processing
          or cloud providers with your own API key.
        </p>

        <div className="space-y-4">
          {/* Provider Selection */}
          <div>
            <label className="mb-2 block text-sm font-medium text-text-secondary">
              Provider
            </label>
            <div className="grid grid-cols-5 gap-2">
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
            <p className="mt-2 text-xs text-text-muted">{currentProviderConfig.description}</p>

            {/* Privacy Notice */}
            {provider === 'ollama' ? (
              <div className="mt-3 flex items-start gap-2 rounded-md border border-success/50 bg-success/10 p-3">
                <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-success" />
                <div className="text-xs">
                  <p className="font-medium text-success">Recommended for Privacy</p>
                  <p className="mt-1 text-text-muted">
                    Ollama runs entirely on your device. Your file contents never leave your
                    computer, ensuring complete privacy and data security.
                  </p>
                </div>
              </div>
            ) : provider === 'ollama_cloud' ? (
              <div className="mt-3 flex items-start gap-2 rounded-md border border-accent/50 bg-accent/10 p-3">
                <Globe className="mt-0.5 h-4 w-4 flex-shrink-0 text-accent" />
                <div className="text-xs">
                  <p className="font-medium text-accent">Ollama Cloud - Powerful GPU Servers</p>
                  <p className="mt-1 text-text-muted">
                    Access larger, more powerful models running on Ollama's high-end GPU infrastructure.
                    Ideal when your local hardware can't handle large models. File contents are processed
                    on Ollama's secure servers. Get your API key at{' '}
                    <a href="https://ollama.com/settings/keys" target="_blank" rel="noopener noreferrer"
                       className="text-accent hover:underline">ollama.com/settings/keys</a>.
                  </p>
                </div>
              </div>
            ) : (
              <div className="mt-3 flex items-start gap-2 rounded-md border border-warning/50 bg-warning/10 p-3">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-warning" />
                <div className="text-xs">
                  <p className="font-medium text-warning">Cloud Provider Notice</p>
                  <p className="mt-1 text-text-muted">
                    Your file contents will be sent to {currentProviderConfig.name}'s servers for
                    processing. If privacy is a concern, consider using Ollama which runs locally on
                    your device.
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
            <p className="mt-1 text-xs text-text-muted">Current: {config?.llm?.model}</p>
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
                {config?.llm?.api_key_configured && config?.llm?.provider === provider ? (
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
                {' '}and run{' '}
                <code className="rounded bg-bg-primary px-1 py-0.5 text-xs">ollama pull {model}</code>
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
            {config?.llm?.api_base && (
              <p className="mt-1 text-xs text-text-muted">Current: {config.llm.api_base}</p>
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
              <span className="text-sm text-error">Failed to save settings</span>
            )}
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-border bg-bg-secondary p-6">
        <div className="mb-4 flex items-center gap-2">
          <Image className="h-5 w-5 text-accent" />
          <h3 className="font-medium text-text-primary">Image Description Model</h3>
        </div>
        <p className="mb-4 text-sm text-text-muted">
          Image descriptions use <strong className="text-text-secondary">Ollama llava</strong> model
          exclusively. This runs locally on your device for privacy.
        </p>

        <div
          className={`mb-4 rounded-md border p-3 ${
            isCheckingLlava
              ? 'border-border bg-bg-tertiary'
              : llavaStatus?.available
                ? 'border-success/50 bg-success/10'
                : 'border-warning/50 bg-warning/10'
          }`}
        >
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
                <Badge variant="success" className="ml-auto">
                  Ready
                </Badge>
              </>
            ) : (
              <>
                <AlertCircle className="h-4 w-4 text-warning" />
                <span className="text-sm text-warning">llava model not available</span>
                <Badge variant="warning" className="ml-auto">
                  Not Ready
                </Badge>
              </>
            )}
          </div>
        </div>

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
    </>
  );
}
