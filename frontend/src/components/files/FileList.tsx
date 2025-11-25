import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import { FileRow } from './FileRow';
import { FileFilters } from './FileFilters';
import { ScanProgress } from '@/components/scan/ScanProgress';
import { Button } from '@/components/common/Button';
import { Spinner } from '@/components/common/Spinner';
import type { FileCategory } from '@/types';

export function FileList() {
  const { currentScanId, isScanning, selectedFileId, setSelectedFileId } =
    useAppStore();

  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<FileCategory | undefined>();
  const [search, setSearch] = useState('');
  const pageSize = 50;

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['files', currentScanId, page, category, search],
    queryFn: () =>
      api.files.list({
        scan_id: currentScanId || undefined,
        category,
        search: search || undefined,
        page,
        page_size: pageSize,
      }),
    enabled: !!currentScanId,
    refetchInterval: isScanning ? 2000 : false,
  });

  useEffect(() => {
    if (!isScanning) {
      refetch();
    }
  }, [isScanning, refetch]);

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  if (!currentScanId) {
    return (
      <div className="flex h-full items-center justify-center text-text-muted">
        Select a folder to scan first
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border p-4">
        <ScanProgress />
        <FileFilters
          category={category}
          onCategoryChange={setCategory}
          search={search}
          onSearchChange={setSearch}
        />
      </div>

      <div className="flex-1 overflow-auto">
        {isLoading && !isScanning ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner size="lg" className="text-accent" />
          </div>
        ) : data?.files.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center gap-3 text-text-muted">
            {isScanning ? (
              <>
                <Spinner size="lg" className="text-accent" />
                <span>Processing files... Files will appear as they are scanned.</span>
              </>
            ) : (
              'No files found'
            )}
          </div>
        ) : (
          <table className="w-full">
            <thead className="sticky top-0 bg-bg-secondary">
              <tr className="border-b border-border text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                <th className="px-4 py-3">File</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Size</th>
                <th className="px-4 py-3">Summary</th>
              </tr>
            </thead>
            <tbody>
              {data?.files.map((file) => (
                <FileRow
                  key={file.id}
                  file={file}
                  isSelected={selectedFileId === file.id}
                  onClick={() =>
                    setSelectedFileId(selectedFileId === file.id ? null : file.id)
                  }
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-border px-4 py-3">
          <span className="text-sm text-text-muted">
            Page {page} of {totalPages} ({data?.total} files)
          </span>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
