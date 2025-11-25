export type FileCategory =
  | 'document'
  | 'spreadsheet'
  | 'presentation'
  | 'image'
  | 'video'
  | 'audio'
  | 'archive'
  | 'code'
  | 'text'
  | 'other';

export type ExtractionStatus = 'pending' | 'success' | 'failed' | 'skipped';

export type ScanStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

export interface FileObject {
  id: string;
  path: string;
  filename: string;
  extension: string;
  mime_type: string;
  size_bytes: number;
  size_human: string;
  created_at: string | null;
  modified_at: string | null;
  accessed_at: string | null;
  is_symlink: boolean;
  category: FileCategory;
  parent_dir: string;
  ai_brief_summary: string;
  ai_summary: string;
  llm_model: string | null;
  exif_data: Record<string, unknown>;
  metadata: Record<string, unknown>;
  extraction_status: ExtractionStatus;
  extraction_error: string | null;
  is_password_protected: boolean;
  scanned_at: string;
  summarized_at: string | null;
}

export interface ScanRequest {
  root_path: string;
  recursive: boolean;
  ignore_patterns?: string[];
  generate_summaries: boolean;
}

export interface ScanResponse {
  scan_id: string;
  root_path: string;
  status: ScanStatus;
  total_files: number;
  processed_files: number;
  failed_files: number;
  started_at: string;
  completed_at: string | null;
}

export interface ScanStatusResponse {
  scan_id: string;
  status: ScanStatus;
  total_files: number;
  processed_files: number;
  failed_files: number;
  files: FileObject[];
}

export interface FileListResponse {
  total: number;
  page: number;
  page_size: number;
  files: FileObject[];
}

export interface LLMConfig {
  provider: string;
  model: string;
  api_base: string | null;
  api_key_configured: boolean;
}

export interface LLMConfigUpdate {
  provider?: string;
  model?: string;
  api_key?: string;
  api_base?: string;
}

export interface AppConfig {
  app_name: string;
  version: string;
  debug: boolean;
  db_path: string;
  max_content_lines: number;
  default_ignore_patterns: string[];
  llm: LLMConfig;
}

export interface CategoryStats {
  [category: string]: {
    count: number;
    total_size: number;
    total_size_human: string;
  };
}

export interface ExtensionStats {
  extension: string;
  count: number;
}
