import { Folder } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import { truncatePath } from '@/lib/utils';

export function Header() {
  const { currentFolderPath, currentView } = useAppStore();

  const titles: Record<string, string> = {
    'add-folder': 'Add Folder',
    folders: 'My Folders',
    files: 'Files',
    settings: 'Settings',
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-bg-secondary px-6">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold text-text-primary">
          {titles[currentView] || 'FileVyasa'}
        </h1>
        {currentFolderPath && currentView === 'files' && (
          <div className="flex items-center gap-2 rounded-md bg-bg-tertiary px-3 py-1.5 text-sm text-text-secondary">
            <Folder className="h-4 w-4" />
            <span title={currentFolderPath}>{truncatePath(currentFolderPath, 40)}</span>
          </div>
        )}
      </div>
    </header>
  );
}
