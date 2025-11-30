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
  FileType2,
} from 'lucide-react';
import type { FileCategory } from '@/types';
import { cn, getCategoryColor } from '@/lib/utils';

interface FileIconProps {
  category: FileCategory;
  extension?: string;
  className?: string;
}

export function FileIcon({ category, extension, className }: FileIconProps) {
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

  // PDF gets a specific icon
  const ext = extension?.toLowerCase().replace('.', '');
  if (ext === 'pdf') {
    return <FileType2 className={cn('h-5 w-5 text-red-500', className)} />;
  }

  const Icon = icons[category] || File;

  return <Icon className={cn('h-5 w-5', getCategoryColor(category), className)} />;
}
