import {
  FolderPlus,
  FolderOpen,
  Files,
  Settings,
  CircleDot,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/stores/appStore';

type View = 'add-folder' | 'folders' | 'files' | 'settings';

const navItems: { id: View; label: string; icon: typeof FolderOpen }[] = [
  { id: 'add-folder', label: 'Add Folder', icon: FolderPlus },
  { id: 'folders', label: 'My Folders', icon: FolderOpen },
  { id: 'files', label: 'Browse', icon: Files },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const {
    currentView,
    setCurrentView,
    backendConnected,
    appName,
    setSettingsSection,
    clearSettingsContext,
  } = useAppStore();

  return (
    <aside className="flex h-full w-56 flex-col border-r border-border bg-bg-secondary">
      <div className="flex items-center gap-2 px-4 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent">
          <Files className="h-5 w-5 text-white" />
        </div>
        <span className="text-lg font-semibold text-text-primary">{appName}</span>
      </div>

      <nav className="flex-1 px-2 py-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => {
                if (item.id === 'settings') {
                  clearSettingsContext();
                  setSettingsSection('overview');
                }
                setCurrentView(item.id);
              }}
              className={cn(
                'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent text-white'
                  : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="border-t border-border px-4 py-3">
        <div className="flex items-center gap-2 text-xs">
          <CircleDot
            className={cn(
              'h-3 w-3',
              backendConnected ? 'text-success' : 'text-error'
            )}
          />
          <span className="text-text-muted">
            Backend {backendConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </aside>
  );
}
