import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, Check, AlertCircle, Server, Cloud } from 'lucide-react';
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

  const [provider, setProvider] = useState<ProviderKey>('ollama');
  const [model, setModel] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiBase, setApiBase] = useState('');
  const [isSaved, setIsSaved] = useState(false);

  // Initialize form with current config
  useEffect(() => {
    if (config) {
      const currentProvider = config.llm.provider as ProviderKey;
      if (PROVIDERS[currentProvider]) {
        setProvider(currentProvider);
      }
      setModel(config.llm.model);
      setApiBase(config.llm.api_base || '');
    }
  }, [config]);

  const mutation = useMutation({
    mutationFn: api.config.updateLLM,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2000);
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
