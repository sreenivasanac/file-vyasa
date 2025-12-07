import type { AppConfig } from '@/types';

interface SettingsGeneralTabProps {
  config: AppConfig | undefined;
}

export function SettingsGeneralTab({ config }: SettingsGeneralTabProps) {
  return (
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
          <span className="text-text-secondary">{config?.max_content_lines}</span>
        </div>
      </div>
    </section>
  );
}
