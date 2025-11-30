import { openPath } from '@tauri-apps/plugin-opener';
import { ExternalLink } from 'lucide-react';
import type { FileObject } from '@/types';
import { FileIcon } from './FileIcon';
import { Badge } from '@/components/common/Badge';
import { cn, getCategoryLabel } from '@/lib/utils';

interface FileRowProps {
  file: FileObject;
  isSelected: boolean;
  onClick: () => void;
}

export function FileRow({ file, isSelected, onClick }: FileRowProps) {
  const handleOpenFile = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await openPath(file.path);
    } catch (err) {
      console.error('Failed to open file:', err);
    }
  };

  return (
    <tr
      onClick={onClick}
      className={cn(
        'group cursor-pointer border-b border-border transition-colors',
        isSelected ? 'bg-accent/10' : 'hover:bg-bg-tertiary'
      )}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <FileIcon category={file.category} extension={file.extension} />
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="truncate font-medium text-text-primary">
                {file.filename}
              </p>
              <button
                onClick={handleOpenFile}
                className="hidden shrink-0 rounded p-1 text-text-muted hover:bg-bg-hover hover:text-text-primary group-hover:flex"
                title="Open file"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </button>
            </div>
            <p className="truncate text-xs text-text-muted" title={file.path}>
              {file.parent_dir}
            </p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <Badge>{getCategoryLabel(file.category)}</Badge>
      </td>
      <td className="px-4 py-3 text-sm text-text-secondary">
        {file.size_human}
      </td>
      <td className="max-w-xs px-4 py-3">
        <p className="truncate text-sm text-text-secondary">
          {file.ai_brief_summary || '-'}
        </p>
      </td>
    </tr>
  );
}
