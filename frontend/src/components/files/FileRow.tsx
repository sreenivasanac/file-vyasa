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
  return (
    <tr
      onClick={onClick}
      className={cn(
        'cursor-pointer border-b border-border transition-colors',
        isSelected ? 'bg-accent/10' : 'hover:bg-bg-tertiary'
      )}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <FileIcon category={file.category} />
          <div className="min-w-0">
            <p className="truncate font-medium text-text-primary">
              {file.filename}
            </p>
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
