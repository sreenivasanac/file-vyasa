import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, Check, AlertCircle } from 'lucide-react';
import { api } from '@/api/client';
import { Button } from '@/components/common/Button';
import { Spinner } from '@/components/common/Spinner';
import { Badge } from '@/components/common/Badge';

export function SettingsPanel() {
  const queryClient = useQueryClient();

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: api.config.get,
  });

  const [provider, setProvider] = useState('');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiBase, setApiBase] = useState('');
  const [isSaved, setIsSaved] = useState(false);

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

  const handleSave = () => {
    mutation.mutate({
      provider: provider || undefined,
      model: model || undefined,
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
          Configure your AI provider for generating file summaries. Bring your
          own API key (BYOK).
        </p>

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              Provider
            </label>
            <input
              type="text"
              placeholder={config?.llm.provider || 'openai'}
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full rounded-md border border-border bg-bg-tertiary px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <p className="mt-1 text-xs text-text-muted">
              Current: {config?.llm.provider}
            </p>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              Model
            </label>
            <input
              type="text"
              placeholder={config?.llm.model || 'gpt-4o-mini'}
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full rounded-md border border-border bg-bg-tertiary px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <p className="mt-1 text-xs text-text-muted">
              Current: {config?.llm.model}
            </p>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              API Key
            </label>
            <input
              type="password"
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full rounded-md border border-border bg-bg-tertiary px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <div className="mt-1 flex items-center gap-2">
              {config?.llm.api_key_configured ? (
                <Badge variant="success">
                  <Check className="mr-1 h-3 w-3" />
                  Configured
                </Badge>
              ) : (
                <Badge variant="warning">
                  <AlertCircle className="mr-1 h-3 w-3" />
                  Not configured
                </Badge>
              )}
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              API Base URL (optional)
            </label>
            <input
              type="text"
              placeholder="https://api.openai.com/v1"
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
