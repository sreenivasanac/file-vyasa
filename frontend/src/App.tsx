import { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { AddFolder } from '@/components/folders/AddFolder';
import { FolderList } from '@/components/folders/FolderList';
import { FileList } from '@/components/files/FileList';
import { FileDetail } from '@/components/files/FileDetail';
import { SettingsPanel } from '@/components/settings/SettingsPanel';
import { useAppStore } from '@/stores/appStore';
import { api } from '@/api/client';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

function AppContent() {
  const { currentView, selectedFileId, setBackendConnected, setAppName } = useAppStore();

  useEffect(() => {
    const checkBackend = async () => {
      try {
        await api.health();
        setBackendConnected(true);
      } catch {
        setBackendConnected(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, [setBackendConnected]);

  useEffect(() => {
    const fetchAppConfig = async () => {
      try {
        const config = await api.config.get();
        setAppName(config.app_name);
        document.title = config.app_name;
      } catch {
        // Keep default app name if config fetch fails
      }
    };
    fetchAppConfig();
  }, [setAppName]);

  const renderContent = () => {
    switch (currentView) {
      case 'add-folder':
        return <AddFolder />;
      case 'folders':
        return <FolderList />;
      case 'files':
        return (
          <div className="flex h-full">
            <div className="flex-1">
              <FileList />
            </div>
            {selectedFileId && <FileDetail />}
          </div>
        );
      case 'settings':
        return <SettingsPanel />;
      default:
        return <FolderList />;
    }
  };

  return <Layout>{renderContent()}</Layout>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
