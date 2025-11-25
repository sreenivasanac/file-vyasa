import { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { FolderPicker } from '@/components/scan/FolderPicker';
import { RecentScans } from '@/components/scan/RecentScans';
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
  const { currentView, selectedFileId, setBackendConnected } = useAppStore();

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
    const interval = setInterval(checkBackend, 5000);
    return () => clearInterval(interval);
  }, [setBackendConnected]);

  const renderContent = () => {
    switch (currentView) {
      case 'scan':
        return <FolderPicker />;
      case 'files':
        return (
          <div className="flex h-full">
            <div className="flex-1">
              <FileList />
            </div>
            {selectedFileId && <FileDetail />}
          </div>
        );
      case 'recent':
        return <RecentScans />;
      case 'settings':
        return <SettingsPanel />;
      default:
        return <FolderPicker />;
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
