import { CheckCircle, Loader, AlertCircle } from 'lucide-react';
import { Badge } from '@/components/common/Badge';
import type { FolderStatus } from '@/types';

interface FolderStatusBadgeProps {
  status: FolderStatus;
}

export function FolderStatusBadge({ status }: FolderStatusBadgeProps) {
  switch (status) {
    case 'idle':
      return (
        <Badge variant="success">
          <CheckCircle className="mr-1 h-3 w-3" />
          Ready
        </Badge>
      );
    case 'syncing':
      return (
        <Badge variant="info">
          <Loader className="mr-1 h-3 w-3 animate-spin" />
          Syncing
        </Badge>
      );
    case 'error':
      return (
        <Badge variant="error">
          <AlertCircle className="mr-1 h-3 w-3" />
          Error
        </Badge>
      );
    case 'cancelled':
      return <Badge variant="warning">Cancelled</Badge>;
    default:
      return <Badge>{status}</Badge>;
  }
}
