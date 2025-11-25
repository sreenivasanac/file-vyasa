import { useQuery } from '@tanstack/react-query';
import { openPath } from '@tauri-apps/plugin-opener';
import { X, ExternalLink, Calendar, HardDrive, FileType, Lock } from 'lucide-react';
import { api } from '@/api/client';
import { useAppStore } from '@/stores/appStore';
import { FileIcon } from './FileIcon';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { Spinner } from '@/components/common/Spinner';
import { formatDate, getCategoryLabel } from '@/lib/utils';

export function FileDetail() {
  const { selectedFileId, setSelectedFileId } = useAppStore();

  const { data: file, isLoading } = useQuery({
    queryKey: ['file', selectedFileId],
    queryFn: () => api.files.get(selectedFileId!),
    enabled: !!selectedFileId,
  });

  if (!selectedFileId) return null;

  return (
    <div className="flex h-full w-96 flex-col border-l border-border bg-bg-secondary">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h3 className="font-medium text-text-primary">File Details</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSelectedFileId(null)}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {isLoading ? (
        <div className="flex flex-1 items-center justify-center">
          <Spinner className="text-accent" />
        </div>
      ) : file ? (
        <div className="flex-1 overflow-auto p-4">
          <div className="mb-6 flex items-start gap-3">
            <FileIcon category={file.category} className="mt-1 h-8 w-8" />
            <div className="min-w-0 flex-1">
              <h4 className="break-words font-medium text-text-primary">
                {file.filename}
              </h4>
              <p className="mt-1 break-all text-xs text-text-muted">
                {file.path}
              </p>
            </div>
          </div>

          <div className="mb-6 flex flex-wrap gap-2">
            <Badge>{getCategoryLabel(file.category)}</Badge>
            {file.is_password_protected && (
              <Badge variant="warning">
                <Lock className="mr-1 h-3 w-3" />
                Protected
              </Badge>
            )}
            {file.is_symlink && <Badge variant="info">Symlink</Badge>}
            <Badge
              variant={
                file.extraction_status === 'success'
                  ? 'success'
                  : file.extraction_status === 'failed'
                    ? 'error'
                    : 'default'
              }
            >
              {file.extraction_status}
            </Badge>
          </div>

          <Section title="File Info">
            <InfoRow
              icon={<FileType className="h-4 w-4" />}
              label="Type"
              value={file.mime_type || file.extension || '-'}
            />
            <InfoRow
              icon={<HardDrive className="h-4 w-4" />}
              label="Size"
              value={file.size_human}
            />
            <InfoRow
              icon={<Calendar className="h-4 w-4" />}
              label="Created"
              value={formatDate(file.created_at)}
            />
            <InfoRow
              icon={<Calendar className="h-4 w-4" />}
              label="Modified"
              value={formatDate(file.modified_at)}
            />
          </Section>

          {(file.ai_brief_summary || file.ai_summary) && (
            <Section title="AI Summary">
              {file.ai_brief_summary && (
                <p className="mb-2 text-sm text-text-secondary">
                  {file.ai_brief_summary}
                </p>
              )}
              {file.ai_summary && (
                <p className="text-sm text-text-muted">{file.ai_summary}</p>
              )}
            </Section>
          )}

          {file.extraction_error && (
            <Section title="Extraction Error">
              <p className="text-sm text-error">{file.extraction_error}</p>
            </Section>
          )}

          {Object.keys(file.exif_data).length > 0 && (
            <Section title="EXIF Data">
              <div className="space-y-1">
                {Object.entries(file.exif_data)
                  .slice(0, 10)
                  .map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <span className="text-text-muted">{key}</span>
                      <span className="text-text-secondary">
                        {String(value)}
                      </span>
                    </div>
                  ))}
              </div>
            </Section>
          )}

          {Object.keys(file.metadata).length > 0 && (
            <Section title="Metadata">
              <div className="space-y-1">
                {Object.entries(file.metadata)
                  .slice(0, 10)
                  .map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs">
                      <span className="text-text-muted">{key}</span>
                      <span className="text-text-secondary">
                        {String(value)}
                      </span>
                    </div>
                  ))}
              </div>
            </Section>
          )}

          <div className="mt-6">
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={async () => {
                try {
                  await openPath(file.path);
                } catch (err) {
                  console.error('Failed to open file:', err);
                }
              }}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Open File
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-6">
      <h5 className="mb-2 text-xs font-medium uppercase tracking-wider text-text-muted">
        {title}
      </h5>
      {children}
    </div>
  );
}

function InfoRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between py-1">
      <div className="flex items-center gap-2 text-text-muted">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <span className="text-sm text-text-secondary">{value}</span>
    </div>
  );
}
