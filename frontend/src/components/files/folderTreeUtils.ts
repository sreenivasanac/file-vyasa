import type { FileObject } from '@/types';

export interface TreeNode {
  name: string;
  path: string;
  isFolder: boolean;
  children: Map<string, TreeNode>;
  file?: FileObject;
  fileCount: number;
  completedCount: number;
}

export function buildTree(files: FileObject[], rootPath: string): TreeNode {
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
export function hasProcessingDescendant(
  folderPath: string,
  processingFilePaths: string[],
): boolean {
  return processingFilePaths.some((filePath) => filePath.startsWith(folderPath + '/'));
}
