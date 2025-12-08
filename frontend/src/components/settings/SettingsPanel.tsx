import { useQuery } from '@tanstack/react-query';
import * as Tabs from '@radix-ui/react-tabs';
import { api } from '@/api/client';
import { Spinner } from '@/components/common/Spinner';
import { BackendDisconnected } from '@/components/common/BackendDisconnected';
import { useAppStore, type SettingsSection } from '@/stores/appStore';
import { cn } from '@/lib/utils';
import { SettingsOverviewTab } from './SettingsOverviewTab';
import { SettingsAiTab } from './SettingsAiTab';
import { SettingsIntegrationsTab } from './SettingsIntegrationsTab';
import { SettingsGeneralTab } from './SettingsGeneralTab';
import { SettingsAddFolderBanner } from './SettingsAddFolderBanner';

export function SettingsPanel() {
  const {
    settingsSection,
    settingsContext,
    setSettingsSection,
    clearSettingsContext,
    setCurrentView,
    backendConnected,
  } = useAppStore();

  const activeTab: SettingsSection = settingsSection ?? 'overview';
  const fromAddFolder = settingsContext?.origin === 'add-folder';
  const highlightLlm = settingsContext?.highlight === 'llm';
  const highlightGoogle = settingsContext?.highlight === 'google-workspace';

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: api.config.get,
  });

  if (!backendConnected) {
    return <BackendDisconnected />;
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" className="text-accent" />
      </div>
    );
  }

  const handleTabChange = (value: string) => {
    setSettingsSection(value as SettingsSection);
  };

  const handleBackToAddFolder = () => {
    clearSettingsContext();
    setSettingsSection('overview');
    setCurrentView('add-folder');
  };

  const handleDismissBanner = () => {
    clearSettingsContext();
  };

  return (
    <div className="mx-auto max-w-3xl p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-text-primary">Settings</h2>
        {config?.app_name && (
          <span className="text-xs text-text-muted">
            Workspace: <span className="text-text-secondary">{config.app_name}</span>
          </span>
        )}
      </div>
      <SettingsAddFolderBanner
        show={fromAddFolder}
        highlightGoogle={highlightGoogle}
        onBack={handleBackToAddFolder}
        onDismiss={handleDismissBanner}
      />

      <Tabs.Root value={activeTab} onValueChange={handleTabChange}>
        <Tabs.List className="mb-6 inline-flex rounded-lg border border-border bg-bg-tertiary p-1 text-sm">
          <Tabs.Trigger
            value="overview"
            className={cn(
              'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
              activeTab === 'overview'
                ? 'bg-bg-primary text-text-primary shadow-sm'
                : 'text-text-muted hover:text-text-primary',
            )}
          >
            Overview
          </Tabs.Trigger>
          <Tabs.Trigger
            value="ai"
            className={cn(
              'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
              activeTab === 'ai'
                ? 'bg-bg-primary text-text-primary shadow-sm'
                : 'text-text-muted hover:text-text-primary',
            )}
          >
            AI &amp; Models
          </Tabs.Trigger>
          <Tabs.Trigger
            value="integrations"
            className={cn(
              'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
              activeTab === 'integrations'
                ? 'bg-bg-primary text-text-primary shadow-sm'
                : 'text-text-muted hover:text-text-primary',
            )}
          >
            Integrations
          </Tabs.Trigger>
          <Tabs.Trigger
            value="general"
            className={cn(
              'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
              activeTab === 'general'
                ? 'bg-bg-primary text-text-primary shadow-sm'
                : 'text-text-muted hover:text-text-primary',
            )}
          >
            General
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="overview" className="space-y-4">
          <SettingsOverviewTab
            config={config}
            onGoAi={() => setSettingsSection('ai')}
            onGoIntegrations={() => setSettingsSection('integrations')}
            onGoGeneral={() => setSettingsSection('general')}
          />
        </Tabs.Content>

        <Tabs.Content value="ai" className="space-y-8">
          <SettingsAiTab config={config} highlightLlm={highlightLlm} />
        </Tabs.Content>

        <Tabs.Content value="integrations" className="space-y-8">
          <SettingsIntegrationsTab config={config} highlightGoogle={highlightGoogle} />
        </Tabs.Content>

        <Tabs.Content value="general" className="space-y-8">
          <SettingsGeneralTab config={config} />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
