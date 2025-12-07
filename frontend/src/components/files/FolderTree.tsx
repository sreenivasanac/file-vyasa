import { useMemo } from 'react';
import type { FileObject } from '@/types';
import { TreeNodeComponent } from './FolderTreeNode';
import { buildTree } from './folderTreeUtils';

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
