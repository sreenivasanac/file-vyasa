import { useState } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import { Button } from './Button';

interface BackendDisconnectedProps {
  variant?: 'full' | 'inline';
  className?: string;
}

export function BackendDisconnected({
  variant = 'full',
  className,
}: BackendDisconnectedProps) {
  const [isRetrying, setIsRetrying] = useState(false);
  const { setBackendConnected } = useAppStore();

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      await api.health();
      setBackendConnected(true);
    } catch {
      setBackendConnected(false);
    } finally {
      setIsRetrying(false);
    }
  };

  if (variant === 'inline') {
    return (
      <div
        className={cn(
          'flex items-center gap-3 rounded-lg border border-warning/30 bg-warning/10 px-4 py-3',
          className
        )}
      >
        <WifiOff className="h-5 w-5 flex-shrink-0 text-warning" />
        <div className="flex-1">
          <p className="text-sm font-medium text-warning">
            Backend server not connected
          </p>
          <p className="text-xs text-text-muted">
            Some features are unavailable. Start the backend server to continue.
          </p>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleRetry}
          disabled={isRetrying}
          className="flex-shrink-0"
        >
          <RefreshCw
            className={cn('mr-1.5 h-3.5 w-3.5', isRetrying && 'animate-spin')}
          />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex h-full flex-col items-center justify-center p-8',
        className
      )}
    >
      <div className="flex max-w-md flex-col items-center text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-warning/20">
          <WifiOff className="h-8 w-8 text-warning" />
        </div>

        <h2 className="mb-2 text-xl font-semibold text-text-primary">
          Backend Server Not Connected
        </h2>

        <p className="mb-6 text-sm text-text-secondary">
          The backend server is not running. Please start it to use FileVyasa.
        </p>

        <div className="mb-6 w-full rounded-lg border border-border bg-bg-tertiary p-4">
          <p className="mb-2 text-xs font-medium text-text-muted">
            Start the server with:
          </p>
          <code className="block rounded bg-bg-primary px-3 py-2 text-sm text-accent">
            cd backend && uv run uvicorn filevyasa.main:app --reload
          </code>
        </div>

        <Button onClick={handleRetry} disabled={isRetrying}>
          <RefreshCw
            className={cn('mr-2 h-4 w-4', isRetrying && 'animate-spin')}
          />
          {isRetrying ? 'Checking...' : 'Retry Connection'}
        </Button>
      </div>
    </div>
  );
}
