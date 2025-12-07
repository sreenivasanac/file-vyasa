import { useState, useMemo } from 'react';
import { openPath } from '@tauri-apps/plugin-opener';
import {
  ChevronRight,
  ChevronDown,
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

interface TreeNode {
  name: string;
  path: string;
  isFolder: boolean;
  children: Map<string, TreeNode>;
  file?: FileObject;
  fileCount: number;
  completedCount: number;
}

interface FolderTreeProps {
  files: FileObject[];
  rootPath: string;
  selectedFileId: string | null;
  onSelectFile: (fileId: string | null) => void;
  isSyncing: boolean;
  totalFiles?: number;
  processedFiles?: number;
  /** Paths of files currently being processed (for spinning animation) */
  processingFilePaths?: string[];
}

function buildTree(files: FileObject[], rootPath: string): TreeNode {
  const root: TreeNode = {
    name: rootPath.split('/').pop() || rootPath,
    path: rootPath,
    isFolder: true,
    children: new Map(),
    fileCount: 0,
    completedCount: 0,
  };

  for (const file of files) {
    const relativePath = file.path.startsWith(rootPath)
      ? file.path.slice(rootPath.length + 1)
      : file.path;

    const parts = relativePath.split('/');
    let current = root;

    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (!current.children.has(part)) {
        current.children.set(part, {
          name: part,
          path: rootPath + '/' + parts.slice(0, i + 1).join('/'),
          isFolder: true,
          children: new Map(),
          fileCount: 0,
          completedCount: 0,
        });
      }
      current = current.children.get(part)!;
    }

    const fileName = parts[parts.length - 1];
    current.children.set(fileName, {
      name: fileName,
      path: file.path,
      isFolder: false,
      children: new Map(),
      file,
      fileCount: 1,
      completedCount: file.ai_brief_summary ? 1 : 0,
    });
  }

  function updateCounts(node: TreeNode): { fileCount: number; completedCount: number } {
    if (!node.isFolder) {
      return { fileCount: node.fileCount, completedCount: node.completedCount };
    }

    let fileCount = 0;
    let completedCount = 0;

    for (const child of node.children.values()) {
      const counts = updateCounts(child);
      fileCount += counts.fileCount;
      completedCount += counts.completedCount;
    }

    node.fileCount = fileCount;
    node.completedCount = completedCount;
    return { fileCount, completedCount };
  }

  updateCounts(root);
  return root;
}

/**
 * Check if any of the processing file paths are descendants of the given folder path.
 */
function hasProcessingDescendant(
  folderPath: string,
  processingFilePaths: string[]
): boolean {
  return processingFilePaths.some((filePath) => filePath.startsWith(folderPath + '/'));
}

export function FolderTree({
  files,
  rootPath,
  selectedFileId,
  onSelectFile,
  isSyncing,
  totalFiles,
  processedFiles,
  processingFilePaths = [],
}: FolderTreeProps) {
  const tree = useMemo(() => buildTree(files, rootPath), [files, rootPath]);

  return (
    <div className="py-2">
      <TreeNodeComponent
        node={tree}
        depth={0}
        selectedFileId={selectedFileId}
        onSelectFile={onSelectFile}
        isSyncing={isSyncing}
        defaultExpanded
        totalFiles={totalFiles}
        processedFiles={processedFiles}
        processingFilePaths={processingFilePaths}
      />
    </div>
  );
}

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

function TreeNodeComponent({
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
  const displayCompleted = isRootNode && processedFiles !== undefined ? processedFiles : node.completedCount;

  const isCompleted = displayCount > 0 && displayCompleted === displayCount;
  // Folder is processing if it has any descendant currently being processed
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
            'text-sm text-text-primary'
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

  // File node
  const isFileProcessing = processingFilePaths.includes(node.path);

  return (
    <div
      onClick={() => onSelectFile(isSelected ? null : node.file!.id)}
      className={cn(
        'group flex cursor-pointer items-center gap-2 rounded px-2 py-1.5',
        'text-sm transition-colors',
        isSelected
          ? 'bg-accent/20 text-text-primary'
          : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
      )}
      style={{ paddingLeft: `${depth * 16 + 8}px` }}
    >
      <div className="w-4" />
      <FileIcon category={node.file!.category} extension={node.file!.extension} className="h-4 w-4" />
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
