import type {
  AppConfig,
  CategoryStats,
  ExtensionStats,
  FileCategory,
  FileListResponse,
  FileObject,
  LLMConfig,
  LLMConfigUpdate,
  ScanRequest,
  ScanResponse,
  ScanStatusResponse,
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

  // Scan endpoints
  scan: {
    start: (data: ScanRequest): Promise<ScanResponse> =>
      request('/scan/start', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    status: (
      scanId: string,
      includeFiles = false
    ): Promise<ScanStatusResponse> =>
      request(`/scan/${scanId}/status?include_files=${includeFiles}`),

    recent: (limit = 10): Promise<ScanResponse[]> =>
      request(`/scan/recent?limit=${limit}`),
  },

  // File endpoints
  files: {
    list: (params: {
      scan_id?: string;
      category?: FileCategory;
      extension?: string;
      search?: string;
      page?: number;
      page_size?: number;
    }): Promise<FileListResponse> => {
      const searchParams = new URLSearchParams();
      if (params.scan_id) searchParams.set('scan_id', params.scan_id);
      if (params.category) searchParams.set('category', params.category);
      if (params.extension) searchParams.set('extension', params.extension);
      if (params.search) searchParams.set('search', params.search);
      if (params.page) searchParams.set('page', params.page.toString());
      if (params.page_size)
        searchParams.set('page_size', params.page_size.toString());
      return request(`/files?${searchParams}`);
    },

    get: (fileId: string): Promise<FileObject> => request(`/files/${fileId}`),

    categoryStats: (scanId?: string): Promise<CategoryStats> => {
      const params = scanId ? `?scan_id=${scanId}` : '';
      return request(`/files/categories/stats${params}`);
    },

    extensionStats: (
      scanId?: string,
      limit = 20
    ): Promise<ExtensionStats[]> => {
      const params = new URLSearchParams();
      if (scanId) params.set('scan_id', scanId);
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
  },
};
