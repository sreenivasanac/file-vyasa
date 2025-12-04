import { cn } from '@/lib/utils';

interface SyncProgressBarProps {
  total: number;
  processed: number;
  variant?: 'accent' | 'warning';
  size?: 'sm' | 'md';
}

export function SyncProgressBar({
  total,
  processed,
  variant = 'accent',
  size = 'md',
}: SyncProgressBarProps) {
  const progress = total > 0 ? Math.round((processed / total) * 100) : 0;

  return (
    <div
      className={cn(
        'overflow-hidden rounded-full bg-bg-tertiary',
        size === 'sm' ? 'h-1.5' : 'h-2'
      )}
    >
      <div
        className={cn(
          'h-full transition-all duration-300',
          variant === 'accent' ? 'bg-accent' : 'bg-warning'
        )}
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}
