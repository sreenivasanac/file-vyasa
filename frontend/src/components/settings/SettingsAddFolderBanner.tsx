import { FolderOpen, X } from 'lucide-react';
import { Button } from '@/components/common/Button';

interface SettingsAddFolderBannerProps {
  show: boolean;
  highlightGoogle: boolean;
  onBack: () => void;
  onDismiss: () => void;
}

export function SettingsAddFolderBanner({
  show,
  highlightGoogle,
  onBack,
  onDismiss,
}: SettingsAddFolderBannerProps) {
  if (!show) return null;

  return (
    <div className="mb-4 flex items-start justify-between rounded-lg border border-accent/60 bg-accent/10 px-4 py-3 text-sm">
      <div>
        <p className="font-medium text-text-primary">You came from Add Folder</p>
        <p className="mt-1 text-xs text-text-muted">
          Configure {highlightGoogle ? 'Google Workspace' : 'AI models'} here, then return to add
          your folder.
        </p>
      </div>
      <div className="ml-4 flex items-center gap-2">
        <Button variant="secondary" size="sm" onClick={onBack}>
          <FolderOpen className="mr-1 h-4 w-4" />
          Back to Add Folder
        </Button>
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-md p-1 text-text-muted hover:bg-bg-tertiary hover:text-text-primary"
          aria-label="Dismiss banner"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
