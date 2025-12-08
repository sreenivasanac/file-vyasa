import type {
  AppConfig,
  CategoryStats,
  ExtensionStats,
  FileCategory,
  FileListResponse,
  FileObject,
  FolderCreateRequest,
  FolderSyncRequest,
  GoogleConfig,
  GoogleConfigUpdate,
  LLMConfig,
  LLMConfigUpdate,
  MonitoredFolder,
} from '@/types';

const API_BASE = 'http://127.0.0.1:8000/api';

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new ApiError(response.status, error);
  }

  return response.json();
}

export const api = {
  // Health check
  health: () => fetch(`${API_BASE.replace('/api', '')}/health`).then((r) => r.json()),

  // Folder endpoints
  folders: {
    add: (data: FolderCreateRequest): Promise<MonitoredFolder> =>
      request('/folders', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    list: (): Promise<MonitoredFolder[]> => request('/folders'),

    get: (folderId: string): Promise<MonitoredFolder> =>
      request(`/folders/${folderId}`),

    delete: (folderId: string): Promise<{ message: string; folder_id: string }> =>
      request(`/folders/${folderId}`, { method: 'DELETE' }),

    sync: (folderId: string, data?: FolderSyncRequest): Promise<MonitoredFolder> =>
      request(`/folders/${folderId}/sync`, {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
      }),

    cancel: (folderId: string): Promise<{ folder_id: string; status: string }> =>
      request(`/folders/${folderId}/cancel`, { method: 'POST' }),

    getProcessing: (folderId: string): Promise<{
      folder_id: string;
      processing_files: Array<{ path: string; filename: string }>;
    }> => request(`/folders/${folderId}/processing`),

    getSyncStatus: (folderId: string): Promise<{
      folder: MonitoredFolder;
      processing_files: Array<{ path: string; filename: string }>;
    }> => request(`/folders/${folderId}/sync-status`),
  },

  // File endpoints
  files: {
    list: (params: {
      folder_id?: string;
      category?: FileCategory;
      extension?: string;
      search?: string;
      page?: number;
      page_size?: number;
    }): Promise<FileListResponse> => {
      const searchParams = new URLSearchParams();
      if (params.folder_id) searchParams.set('folder_id', params.folder_id);
      if (params.category) searchParams.set('category', params.category);
      if (params.extension) searchParams.set('extension', params.extension);
      if (params.search) searchParams.set('search', params.search);
      if (params.page) searchParams.set('page', params.page.toString());
      if (params.page_size)
        searchParams.set('page_size', params.page_size.toString());
      return request(`/files/?${searchParams}`);
    },

    get: (fileId: string): Promise<FileObject> => request(`/files/${fileId}`),

    categoryStats: (folderId?: string): Promise<CategoryStats> => {
      const params = folderId ? `?folder_id=${folderId}` : '';
      return request(`/files/categories/stats${params}`);
    },

    extensionStats: (
      folderId?: string,
      limit = 20
    ): Promise<ExtensionStats[]> => {
      const params = new URLSearchParams();
      if (folderId) params.set('folder_id', folderId);
      params.set('limit', limit.toString());
      return request(`/files/extensions/stats?${params}`);
    },
  },

  // Config endpoints
  config: {
    get: (): Promise<AppConfig> => request('/config'),

    updateLLM: (data: LLMConfigUpdate): Promise<LLMConfig> =>
      request('/config/llm', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    supportedExtensions: (): Promise<{
      text: string[];
      document: string[];
      image: string[];
    }> => request('/config/supported-extensions'),

    checkLlavaStatus: (): Promise<{ available: boolean; reason: string | null }> =>
      request('/config/llava-status'),

    updateGoogle: (data: GoogleConfigUpdate): Promise<GoogleConfig> =>
      request('/config/google', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    verifyGoogle: (): Promise<{
      success: boolean;
      message: string;
      service_account_email?: string;
    }> =>
      request('/config/google/verify', {
        method: 'POST',
      }),
  },
};
