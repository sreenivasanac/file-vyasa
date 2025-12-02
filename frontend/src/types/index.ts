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

export type FolderStatus = 'idle' | 'syncing' | 'cancelled' | 'error';

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

// Monitored Folder types
export interface MonitoredFolder {
  id: string;
  root_path: string;
  name: string;
  status: FolderStatus;
  last_synced_at: string | null;
  last_llm_model: string | null;
  total_files: number;
  processed_files: number;
  failed_files: number;
  // AI processing options
  generate_document_summaries: boolean;
  generate_image_descriptions: boolean;
  extract_media_transcriptions: boolean;
  ignore_patterns: string[];
  created_at: string;
}

export interface FolderCreateRequest {
  root_path: string;
  // AI processing options
  generate_document_summaries: boolean;
  generate_image_descriptions: boolean;
  extract_media_transcriptions: boolean;
  ignore_patterns?: string[];
}

export interface FolderSyncRequest {
  generate_document_summaries?: boolean;
  generate_image_descriptions?: boolean;
  extract_media_transcriptions?: boolean;
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

export interface GoogleConfig {
  credentials_configured: boolean;
  credentials_path: string | null;
}

export interface GoogleConfigUpdate {
  credentials_path?: string;
}

export interface AppConfig {
  app_name: string;
  version: string;
  debug: boolean;
  db_path: string;
  max_content_lines: number;
  default_ignore_patterns: string[];
  llm: LLMConfig;
  google: GoogleConfig;
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
