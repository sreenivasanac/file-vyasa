# FileVyasa Backend

Python FastAPI backend service for FileVyasa (v1.1.0).

## What It Does

- **Folder Monitoring** — Track folders and detect file changes on re-sync with parallel processing
- **Content Extraction** — Extract text/metadata from 30+ file types including OCR for image-based PDFs
- **AI Features** — Document summarization (100+ LLM providers via LiteLLM), image description (Ollama llava), media transcription (faster-whisper)
- **Google Workspace** — Extract content from Google Docs and Sheets via service account
- **REST API** — Full-featured endpoints for the frontend desktop app

## Quick Start

```bash
uv sync
uv run python run.py
```

API runs at `http://127.0.0.1:8000`. Visit `/docs` for Swagger UI.

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `FILEVYASA_LLM_API_KEY` | API key for cloud LLM providers |
| `FILEVYASA_GOOGLE_CREDENTIALS_PATH` | Path to Google service account JSON |

### Settings (`config/settings.yaml`)

```yaml
llm:
  provider: ollama      # ollama, openai, anthropic, gemini, groq, deepseek, together_ai, fireworks_ai
  model: llama3.2
  api_base: http://localhost:11434

extraction:
  max_content_lines: 50

sync:
  extraction_workers: 16   # Parallel content extraction
  ai_workers: 8            # Parallel AI processing
  db_batch_size: 1         # 1 = real-time UI updates
  enable_parallel: true

scan:
  ignore_file_patterns:    # Files to skip (glob patterns)
    - .DS_Store
    - '*.pyc'
  ignore_folder_names:     # Folders to skip entirely
    - node_modules
    - .git
    - __pycache__
```

## API Overview

### Folders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/folders` | Add folder to monitor (auto-syncs) |
| GET | `/api/folders` | List monitored folders |
| GET | `/api/folders/{id}` | Get folder details |
| POST | `/api/folders/{id}/sync` | Re-sync folder |
| POST | `/api/folders/{id}/cancel` | Cancel ongoing sync |
| GET | `/api/folders/{id}/sync-status` | Get sync status + processing files |
| GET | `/api/folders/{id}/processing` | Get files currently being processed |
| DELETE | `/api/folders/{id}` | Remove folder from monitoring |

### Files
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/files/` | List files (with filtering, pagination) |
| GET | `/api/files/{id}` | Get file details |
| GET | `/api/files/lookup` | Lookup by id, path, or inode |

**Filter parameters:** `folder_id`, `categories`, `extraction_status`, `extension`, `search`, `page`, `page_size`

### Config
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config/` | Get current settings |
| POST | `/api/config/llm` | Update LLM settings |
| POST | `/api/config/google` | Update Google credentials path |
| POST | `/api/config/google/verify` | Verify Google credentials |
| GET | `/api/config/supported-extensions` | List all supported file types |
| GET | `/api/config/llava-status` | Check if Ollama llava is available |

## Architecture

```
filevyasa/
├── api/
│   ├── app.py         # FastAPI application setup
│   └── routes/        # API endpoints (folders, files, config)
├── db/
│   ├── connection.py  # SQLite session management
│   ├── tables.py      # SQLAlchemy models
│   └── folder_repository.py  # Folder CRUD operations
├── extractor/
│   ├── factory.py     # Extractor selection logic
│   ├── base.py        # Base extractor class
│   └── *_extractor.py # Type-specific extractors
├── llm/
│   ├── summarizer.py      # Document summarization
│   ├── image_describer.py # Image description via llava
│   ├── response_parser.py # Parse AI responses
│   └── health.py          # LLM health checks
├── scanner/           # Directory walking with ignore patterns
├── sync/
│   ├── service.py     # Main sync orchestration
│   ├── processing_tracker.py  # Track files being processed
│   └── cancellation.py  # Sync cancellation support
├── models/
│   ├── file_object.py # FileObject Pydantic schema
│   ├── folder.py      # Folder schemas
│   └── enums.py       # FileCategory, ExtractionStatus, etc.
└── config.py          # Settings management
```

### Extractors

Each file type has a dedicated extractor:

| Extractor | File Types | Features |
|-----------|------------|----------|
| **TextExtractor** | TXT, MD, RTF | Plain text extraction |
| **PDFExtractor** | PDF | Text extraction + OCR via python-doctr |
| **OfficeExtractor** | DOCX, XLSX, PPTX | Via markitdown + python-docx/openpyxl/python-pptx |
| **NotebookExtractor** | IPYNB | Cell content extraction |
| **WebContentExtractor** | HTML, HTM, XML | Web page content |
| **ImageExtractor** | JPG, PNG, HEIC, etc. | EXIF metadata via exifread |
| **MediaExtractor** | MP3, MP4, WAV, etc. | Metadata + transcription via faster-whisper |
| **CodeExtractor** | PY, JS, TS, etc. | Metadata only (language detection) |
| **ArchiveExtractor** | ZIP, TAR, GZ, etc. | Metadata only (listing contents) |
| **GoogleDocsExtractor** | gdoc, gsheet | Google Workspace API extraction |
| **NonContentExtractor** | Various | Files without extractable content |

### FileObject Schema

Key fields stored for each file:
- **Identifiers:** id, path, filename, extension, mime_type, inode
- **Metadata:** size_bytes, created_at, modified_at, is_symlink, category
- **Content:** content_preview (first N lines as markdown)
- **EXIF/Metadata:** exif_data, metadata dictionaries
- **AI Fields:** ai_brief_summary (~2 lines), ai_summary (~4 lines), llm_model
- **Status:** extraction_status (pending/extracting/completed/failed/skipped), extraction_error, is_password_protected
- **Timestamps:** scanned_at, summarized_at, last_extracted_at, last_ai_processed_at

## Development

```bash
# Install with dev dependencies
uv sync --dev

# Run linter
uv run ruff check .

# Format code
uv run ruff format .

# Run tests
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/test_scanner.py -v
```

### Database

SQLite database stored at `.filevyasa/app.db`. Tables:
- `monitored_folders` — Tracked folders with sync settings
- `file_objects` — All scanned files with metadata and AI summaries
