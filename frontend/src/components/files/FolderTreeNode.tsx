import { useMemo, useState } from 'react';
import { openPath } from '@tauri-apps/plugin-opener';
import {
  ChevronDown,
  ChevronRight,
  Folder,
  FolderOpen,
  CheckCircle,
  Loader,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';
import { FileIcon } from './FileIcon';
import { cn } from '@/lib/utils';
import type { FileObject } from '@/types';
import type { TreeNode } from './folderTreeUtils';
import { hasProcessingDescendant } from './folderTreeUtils';

interface TreeNodeComponentProps {
  node: TreeNode;
  depth: number;
  selectedFileId: string | null;
  onSelectFile: (fileId: string | null) => void;
  isSyncing: boolean;
  defaultExpanded?: boolean;
  totalFiles?: number;
  processedFiles?: number;
  processingFilePaths: string[];
}

export function TreeNodeComponent({
  node,
  depth,
  selectedFileId,
  onSelectFile,
  isSyncing,
  defaultExpanded = false,
  totalFiles,
  processedFiles,
  processingFilePaths,
}: TreeNodeComponentProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const isRootNode = depth === 0;
  const displayCount = isRootNode && totalFiles !== undefined ? totalFiles : node.fileCount;
  const displayCompleted =
    isRootNode && processedFiles !== undefined ? processedFiles : node.completedCount;

  const isCompleted = displayCount > 0 && displayCompleted === displayCount;
  const isProcessing = isSyncing && hasProcessingDescendant(node.path, processingFilePaths);
  const isSelected = node.file?.id === selectedFileId;

  const sortedChildren = useMemo(() => {
    const children = Array.from(node.children.values());
    return children.sort((a, b) => {
      if (a.isFolder && !b.isFolder) return -1;
      if (!a.isFolder && b.isFolder) return 1;
      return a.name.localeCompare(b.name);
    });
  }, [node.children]);

  const handleOpenFolder = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await openPath(node.path);
    } catch (err) {
      console.error('Failed to open folder:', err);
    }
  };

  const handleOpenFile = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await openPath(node.path);
    } catch (err) {
      console.error('Failed to open file:', err);
    }
  };

  if (node.isFolder) {
    return (
      <div>
        <div
          onClick={() => setIsExpanded(!isExpanded)}
          className={cn(
            'group flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-bg-tertiary',
            'text-sm text-text-primary',
          )}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-text-muted" />
          ) : (
            <ChevronRight className="h-4 w-4 text-text-muted" />
          )}
          {isExpanded ? (
            <FolderOpen className="h-4 w-4 text-yellow-500" />
          ) : (
            <Folder className="h-4 w-4 text-yellow-500" />
          )}
          <span className="truncate">{node.name}</span>
          <button
            onClick={handleOpenFolder}
            className="hidden shrink-0 rounded p-1 text-text-muted hover:bg-bg-hover hover:text-text-primary group-hover:flex"
            title="Open in Finder"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </button>
          <div className="flex-1" />
          <StatusIndicator
            isCompleted={isCompleted}
            isProcessing={isProcessing}
            count={displayCount}
            completedCount={displayCompleted}
          />
        </div>
        {isExpanded && (
          <div>
            {sortedChildren.map((child) => (
              <TreeNodeComponent
                key={child.path}
                node={child}
                depth={depth + 1}
                selectedFileId={selectedFileId}
                onSelectFile={onSelectFile}
                isSyncing={isSyncing}
                processingFilePaths={processingFilePaths}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  const isFileProcessing = processingFilePaths.includes(node.path);

  return (
    <div
      onClick={() => onSelectFile(isSelected ? null : node.file!.id)}
      className={cn(
        'group flex cursor-pointer items-center gap-2 rounded px-2 py-1.5',
        'text-sm transition-colors',
        isSelected
          ? 'bg-accent/20 text-text-primary'
          : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary',
      )}
      style={{ paddingLeft: `${depth * 16 + 8}px` }}
    >
      <div className="w-4" />
      <FileIcon
        category={node.file!.category}
        extension={node.file!.extension}
        className="h-4 w-4"
      />
      <span className="truncate" title={node.name}>
        {node.name}
      </span>
      <button
        onClick={handleOpenFile}
        className="hidden shrink-0 rounded p-1 text-text-muted hover:bg-bg-hover hover:text-text-primary group-hover:flex"
        title="Open file"
      >
        <ExternalLink className="h-3.5 w-3.5" />
      </button>
      <div className="flex-1" />
      <FileStatusIndicator file={node.file!} isProcessing={isFileProcessing} />
    </div>
  );
}

function StatusIndicator({
  isCompleted,
  isProcessing,
  count,
  completedCount,
}: {
  isCompleted: boolean;
  isProcessing: boolean;
  count: number;
  completedCount: number;
}) {
  if (count === 0) return null;

  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs text-text-muted">
        {completedCount}/{count}
      </span>
      {isCompleted ? (
        <CheckCircle className="h-3.5 w-3.5 text-success" />
      ) : isProcessing ? (
        <Loader className="h-3.5 w-3.5 animate-spin text-accent" />
      ) : (
        <AlertCircle className="h-3.5 w-3.5 text-warning" />
      )}
    </div>
  );
}

function FileStatusIndicator({
  file,
  isProcessing,
}: {
  file: FileObject;
  isProcessing: boolean;
}) {
  const hasAISummary = !!file.ai_brief_summary;

  if (isProcessing) {
    return <Loader className="h-3.5 w-3.5 animate-spin text-accent" />;
  }

  if (hasAISummary) {
    return <CheckCircle className="h-3.5 w-3.5 text-success" />;
  }

  return <AlertCircle className="h-3.5 w-3.5 text-warning" />;
}
