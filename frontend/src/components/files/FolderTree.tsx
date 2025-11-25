import { useState, useMemo } from 'react';
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  CheckCircle,
  Loader,
  AlertCircle,
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
  isScanning: boolean;
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
    // Get relative path from root
    const relativePath = file.path.startsWith(rootPath)
      ? file.path.slice(rootPath.length + 1)
      : file.path;

    const parts = relativePath.split('/');
    let current = root;

    // Navigate/create folder structure
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

    // Add file
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

  // Calculate counts
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

export function FolderTree({
  files,
  rootPath,
  selectedFileId,
  onSelectFile,
  isScanning,
}: FolderTreeProps) {
  const tree = useMemo(() => buildTree(files, rootPath), [files, rootPath]);

  return (
    <div className="py-2">
      <TreeNodeComponent
        node={tree}
        depth={0}
        selectedFileId={selectedFileId}
        onSelectFile={onSelectFile}
        isScanning={isScanning}
        defaultExpanded
      />
    </div>
  );
}

interface TreeNodeComponentProps {
  node: TreeNode;
  depth: number;
  selectedFileId: string | null;
  onSelectFile: (fileId: string | null) => void;
  isScanning: boolean;
  defaultExpanded?: boolean;
}

function TreeNodeComponent({
  node,
  depth,
  selectedFileId,
  onSelectFile,
  isScanning,
  defaultExpanded = false,
}: TreeNodeComponentProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const isCompleted = node.fileCount > 0 && node.completedCount === node.fileCount;
  const isProcessing = isScanning && node.completedCount < node.fileCount;
  const isSelected = node.file?.id === selectedFileId;

  // Sort children: folders first, then files, alphabetically
  const sortedChildren = useMemo(() => {
    const children = Array.from(node.children.values());
    return children.sort((a, b) => {
      if (a.isFolder && !b.isFolder) return -1;
      if (!a.isFolder && b.isFolder) return 1;
      return a.name.localeCompare(b.name);
    });
  }, [node.children]);

  if (node.isFolder) {
    return (
      <div>
        <div
          onClick={() => setIsExpanded(!isExpanded)}
          className={cn(
            'flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-bg-tertiary',
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
          <span className="flex-1 truncate">{node.name}</span>
          <StatusIndicator
            isCompleted={isCompleted}
            isProcessing={isProcessing}
            count={node.fileCount}
            completedCount={node.completedCount}
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
                isScanning={isScanning}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // File node
  return (
    <div
      onClick={() => onSelectFile(isSelected ? null : node.file!.id)}
      className={cn(
        'flex cursor-pointer items-center gap-2 rounded px-2 py-1.5',
        'text-sm transition-colors',
        isSelected
          ? 'bg-accent/20 text-text-primary'
          : 'text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
      )}
      style={{ paddingLeft: `${depth * 16 + 8}px` }}
    >
      <div className="w-4" /> {/* Spacer for alignment */}
      <FileIcon category={node.file!.category} className="h-4 w-4" />
      <span className="flex-1 truncate" title={node.name}>
        {node.name}
      </span>
      <FileStatusIndicator file={node.file!} isScanning={isScanning} />
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
  isScanning,
}: {
  file: FileObject;
  isScanning: boolean;
}) {
  const hasAISummary = !!file.ai_brief_summary;

  if (hasAISummary) {
    return <CheckCircle className="h-3.5 w-3.5 text-success" />;
  }

  if (isScanning) {
    return <Loader className="h-3.5 w-3.5 animate-spin text-accent" />;
  }

  return <AlertCircle className="h-3.5 w-3.5 text-warning" />;
}
