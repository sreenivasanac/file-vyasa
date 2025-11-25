import { Search, X } from 'lucide-react';
import * as Select from '@radix-ui/react-select';
import { ChevronDown, Check } from 'lucide-react';
import type { FileCategory } from '@/types';
import { getCategoryLabel } from '@/lib/utils';

interface FileFiltersProps {
  category: FileCategory | undefined;
  onCategoryChange: (category: FileCategory | undefined) => void;
  search: string;
  onSearchChange: (search: string) => void;
}

const categories: FileCategory[] = [
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

export function FileFilters({
  category,
  onCategoryChange,
  search,
  onSearchChange,
}: FileFiltersProps) {
  return (
    <div className="mt-4 flex items-center gap-4">
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

      <Select.Root
        value={category || 'all'}
        onValueChange={(value) =>
          onCategoryChange(value === 'all' ? undefined : (value as FileCategory))
        }
      >
        <Select.Trigger className="inline-flex h-10 w-40 items-center justify-between rounded-md border border-border bg-bg-tertiary px-3 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent">
          <Select.Value placeholder="All Categories" />
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
                <Select.ItemText>All Categories</Select.ItemText>
                <Select.ItemIndicator className="absolute left-2">
                  <Check className="h-4 w-4" />
                </Select.ItemIndicator>
              </Select.Item>

              {categories.map((cat) => (
                <Select.Item
                  key={cat}
                  value={cat}
                  className="relative flex h-9 cursor-pointer items-center rounded-sm px-8 text-sm text-text-primary outline-none hover:bg-bg-tertiary data-[highlighted]:bg-bg-tertiary"
                >
                  <Select.ItemText>{getCategoryLabel(cat)}</Select.ItemText>
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
