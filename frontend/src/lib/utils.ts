import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { FileCategory } from '@/types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getCategoryColor(category: FileCategory): string {
  const colors: Record<FileCategory, string> = {
    document: 'text-blue-400',
    spreadsheet: 'text-green-400',
    presentation: 'text-orange-400',
    image: 'text-pink-400',
    video: 'text-purple-400',
    audio: 'text-cyan-400',
    archive: 'text-yellow-400',
    code: 'text-emerald-400',
    text: 'text-gray-400',
    other: 'text-zinc-400',
  };
  return colors[category] || colors.other;
}

export function getCategoryLabel(category: FileCategory): string {
  const labels: Record<FileCategory, string> = {
    document: 'Document',
    spreadsheet: 'Spreadsheet',
    presentation: 'Presentation',
    image: 'Image',
    video: 'Video',
    audio: 'Audio',
    archive: 'Archive',
    code: 'Code',
    text: 'Text',
    other: 'Other',
  };
  return labels[category] || 'Other';
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '-';
  }
}

export function truncatePath(path: string, maxLength = 50): string {
  if (path.length <= maxLength) return path;
  const parts = path.split('/');
  if (parts.length <= 5) return path;
  return `.../${parts.slice(-4).join('/')}`;
}

/**
 * Format milliseconds to human-readable duration (e.g., "1m 30s", "2h 15m").
 */
export function formatDuration(ms: number): string {
  if (ms < 60000) return `${Math.ceil(ms / 1000)}s`;
  if (ms < 3600000) {
    const mins = Math.floor(ms / 60000);
    const secs = Math.ceil((ms % 60000) / 1000);
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  }
  const hours = Math.floor(ms / 3600000);
  const mins = Math.ceil((ms % 3600000) / 60000);
  return `${hours}h ${mins}m`;
}
