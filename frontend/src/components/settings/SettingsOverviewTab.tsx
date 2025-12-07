import type { AppConfig } from '@/types';
import { Button } from '@/components/common/Button';

interface SettingsOverviewTabProps {
  config: AppConfig | undefined;
  onGoAi: () => void;
  onGoIntegrations: () => void;
  onGoGeneral: () => void;
}

export function SettingsOverviewTab({
  config,
  onGoAi,
  onGoIntegrations,
  onGoGeneral,
}: SettingsOverviewTabProps) {
  return (
    <section className="rounded-lg border border-border bg-bg-secondary p-6">
      <h3 className="mb-2 text-sm font-medium text-text-primary">Quick overview</h3>
      <p className="text-xs text-text-muted">
        Use these sections to control your AI models, Google Workspace integration, and app
        information.
      </p>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <div className="flex flex-col justify-between rounded-md border border-border bg-bg-tertiary p-3 text-xs">
          <div>
            <p className="mb-1 font-medium text-text-secondary">AI &amp; Models</p>
            <p className="text-text-muted">
              {config?.llm ? `${config.llm.provider}/${config.llm.model}` : 'Not configured yet'}
            </p>
            <p className="mt-1 text-[11px] text-text-muted">
              Choose your default LLM for document summaries and manage the local image description
              model.
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            className="mt-3 self-start text-[11px] h-7 px-2"
            onClick={onGoAi}
          >
            Open AI &amp; Models
          </Button>
        </div>
        <div className="flex flex-col justify-between rounded-md border border-border bg-bg-tertiary p-3 text-xs">
          <div>
            <p className="mb-1 font-medium text-text-secondary">Google Workspace</p>
            <p className="text-text-muted">
              {config?.google?.credentials_configured ? 'Connected' : 'Not connected'}
            </p>
            <p className="mt-1 text-[11px] text-text-muted">
              Connect a service account to read Google Docs, Sheets, Slides, and other Workspace
              files from your monitored folders.
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            className="mt-3 self-start text-[11px] h-7 px-2"
            onClick={onGoIntegrations}
          >
            Open Integrations
          </Button>
        </div>
        <div className="flex flex-col justify-between rounded-md border border-border bg-bg-tertiary p-3 text-xs">
          <div>
            <p className="mb-1 font-medium text-text-secondary">App</p>
            <p className="text-text-muted">
              {config?.version ? `v${config.version}` : 'Version unknown'}
            </p>
            <p className="mt-1 text-[11px] text-text-muted">
              See app name, database path, and limits for how much content is indexed from your
              files.
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            className="mt-3 self-start text-[11px] h-7 px-2"
            onClick={onGoGeneral}
          >
            Open General
          </Button>
        </div>
      </div>
    </section>
  );
}
