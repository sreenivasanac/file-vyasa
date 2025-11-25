import {
  FileText,
  FileSpreadsheet,
  Presentation,
  Image,
  Video,
  Music,
  Archive,
  FileCode,
  File,
} from 'lucide-react';
import type { FileCategory } from '@/types';
import { cn, getCategoryColor } from '@/lib/utils';

interface FileIconProps {
  category: FileCategory;
  className?: string;
}

export function FileIcon({ category, className }: FileIconProps) {
  const icons: Record<FileCategory, typeof FileText> = {
    document: FileText,
    spreadsheet: FileSpreadsheet,
    presentation: Presentation,
    image: Image,
    video: Video,
    audio: Music,
    archive: Archive,
    code: FileCode,
    text: FileText,
    other: File,
  };

  const Icon = icons[category] || File;

  return <Icon className={cn('h-5 w-5', getCategoryColor(category), className)} />;
}
