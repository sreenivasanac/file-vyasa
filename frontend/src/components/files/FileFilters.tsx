import { useRef, useState, useEffect } from 'react';
import { Search, X, ChevronDown, Check } from 'lucide-react';
import * as Select from '@radix-ui/react-select';
import type { ExtractionStatus, FileCategory, FilenameQuality } from '@/types';
import { getCategoryLabel } from '@/lib/utils';

interface FileFiltersProps {
  categories: FileCategory[];
  onCategoriesChange: (categories: FileCategory[]) => void;
  extractionStatus: ExtractionStatus | undefined;
  onExtractionStatusChange: (status: ExtractionStatus | undefined) => void;
  filenameQuality: FilenameQuality | undefined;
  onFilenameQualityChange: (quality: FilenameQuality | undefined) => void;
  search: string;
  onSearchChange: (search: string) => void;
}

const allCategories: FileCategory[] = [
  'document',
  'spreadsheet',
  'presentation',
  'image',
  'video',
  'audio',
  'archive',
  'code',
  'text',
  'other',
];

const statusLabels: Record<ExtractionStatus, string> = {
  pending: 'Pending',
  success: 'Completed',
  failed: 'Failed',
  skipped: 'Skipped',
};

const filenameQualityLabels: Record<FilenameQuality, string> = {
  good: 'Good',
  acceptable: 'Acceptable',
  poor: 'Poor',
  meaningless: 'Meaningless',
};

function CategoryMultiSelect({
  selected,
  onChange,
}: {
  selected: FileCategory[];
  onChange: (categories: FileCategory[]) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleCategory = (cat: FileCategory) => {
    if (selected.includes(cat)) {
      onChange(selected.filter((c) => c !== cat));
    } else {
      onChange([...selected, cat]);
    }
  };

  const selectAll = () => onChange([...allCategories]);
  const clearAll = () => onChange([]);

  const displayText = selected.length === 0
    ? 'All Categories'
    : selected.length === allCategories.length
      ? 'All Categories'
      : `Categories (${selected.length})`;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex h-10 w-44 items-center justify-between rounded-md border border-border bg-bg-tertiary px-3 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
      >
        <span className="truncate">{displayText}</span>
        <ChevronDown className="h-4 w-4 flex-shrink-0 text-text-muted" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full z-50 mt-1 w-48 rounded-md border border-border bg-bg-secondary shadow-lg">
          <div className="flex border-b border-border p-2">
            <button
              type="button"
              onClick={selectAll}
              className="flex-1 rounded px-2 py-1 text-xs text-text-muted hover:bg-bg-tertiary hover:text-text-primary"
            >
              Select All
            </button>
            <button
              type="button"
              onClick={clearAll}
              className="flex-1 rounded px-2 py-1 text-xs text-text-muted hover:bg-bg-tertiary hover:text-text-primary"
            >
              Clear
            </button>
          </div>
          <div className="max-h-64 overflow-y-auto p-1">
            {allCategories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => toggleCategory(cat)}
                className="flex w-full cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm text-text-primary hover:bg-bg-tertiary"
              >
                <div className={`flex h-4 w-4 items-center justify-center rounded border ${
                  selected.includes(cat)
                    ? 'border-accent bg-accent'
                    : 'border-border bg-bg-tertiary'
                }`}>
                  {selected.includes(cat) && <Check className="h-3 w-3 text-white" />}
                </div>
                {getCategoryLabel(cat)}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function FileFilters({
  categories,
  onCategoriesChange,
  extractionStatus,
  onExtractionStatusChange,
  filenameQuality,
  onFilenameQualityChange,
  search,
  onSearchChange,
}: FileFiltersProps) {
  return (
    <div className="mt-4 flex items-center gap-3">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          placeholder="Search files..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full rounded-md border border-border bg-bg-tertiary py-2 pl-10 pr-10 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
        {search && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      <CategoryMultiSelect selected={categories} onChange={onCategoriesChange} />

      <Select.Root
        value={extractionStatus || 'all'}
        onValueChange={(value) =>
          onExtractionStatusChange(value === 'all' ? undefined : (value as ExtractionStatus))
        }
      >
        <Select.Trigger className="inline-flex h-10 w-36 items-center justify-between rounded-md border border-border bg-bg-tertiary px-3 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent">
          <Select.Value placeholder="All Status" />
          <Select.Icon>
            <ChevronDown className="h-4 w-4 text-text-muted" />
          </Select.Icon>
        </Select.Trigger>

        <Select.Portal>
          <Select.Content className="overflow-hidden rounded-md border border-border bg-bg-secondary shadow-lg">
            <Select.Viewport className="p-1">
              <Select.Item
                value="all"
                className="relative flex h-9 cursor-pointer items-center rounded-sm px-8 text-sm text-text-primary outline-none hover:bg-bg-tertiary data-[highlighted]:bg-bg-tertiary"
              >
                <Select.ItemText>All Status</Select.ItemText>
                <Select.ItemIndicator className="absolute left-2">
                  <Check className="h-4 w-4" />
                </Select.ItemIndicator>
              </Select.Item>

              {(Object.keys(statusLabels) as ExtractionStatus[]).map((status) => (
                <Select.Item
                  key={status}
                  value={status}
                  className="relative flex h-9 cursor-pointer items-center rounded-sm px-8 text-sm text-text-primary outline-none hover:bg-bg-tertiary data-[highlighted]:bg-bg-tertiary"
                >
                  <Select.ItemText>{statusLabels[status]}</Select.ItemText>
                  <Select.ItemIndicator className="absolute left-2">
                    <Check className="h-4 w-4" />
                  </Select.ItemIndicator>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>

      <Select.Root
        value={filenameQuality || 'all'}
        onValueChange={(value) =>
          onFilenameQualityChange(value === 'all' ? undefined : (value as FilenameQuality))
        }
      >
        <Select.Trigger className="inline-flex h-10 w-40 items-center justify-between rounded-md border border-border bg-bg-tertiary px-3 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent">
          <Select.Value placeholder="All Quality" />
          <Select.Icon>
            <ChevronDown className="h-4 w-4 text-text-muted" />
          </Select.Icon>
        </Select.Trigger>

        <Select.Portal>
          <Select.Content className="overflow-hidden rounded-md border border-border bg-bg-secondary shadow-lg">
            <Select.Viewport className="p-1">
              <Select.Item
                value="all"
                className="relative flex h-9 cursor-pointer items-center rounded-sm px-8 text-sm text-text-primary outline-none hover:bg-bg-tertiary data-[highlighted]:bg-bg-tertiary"
              >
                <Select.ItemText>All Quality</Select.ItemText>
                <Select.ItemIndicator className="absolute left-2">
                  <Check className="h-4 w-4" />
                </Select.ItemIndicator>
              </Select.Item>

              {(Object.keys(filenameQualityLabels) as FilenameQuality[]).map((quality) => (
                <Select.Item
                  key={quality}
                  value={quality}
                  className="relative flex h-9 cursor-pointer items-center rounded-sm px-8 text-sm text-text-primary outline-none hover:bg-bg-tertiary data-[highlighted]:bg-bg-tertiary"
                >
                  <Select.ItemText>{filenameQualityLabels[quality]}</Select.ItemText>
                  <Select.ItemIndicator className="absolute left-2">
                    <Check className="h-4 w-4" />
                  </Select.ItemIndicator>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>
    </div>
  );
}
