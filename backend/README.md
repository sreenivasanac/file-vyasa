# FileVyasa Backend

Python FastAPI backend service for FileVyasa.

## What It Does

- **Folder Monitoring** — Track folders and detect file changes on re-sync
- **Content Extraction** — Extract text/metadata from 30+ file types
- **AI Features** — Document summarization, image description, media transcription
- **REST API** — Endpoints for the frontend desktop app

## Quick Start

```bash
uv sync
uv run python run.py
```

API runs at `http://127.0.0.1:8000`. Visit `/docs` for Swagger UI.

## Configuration

**LLM API Key** (`.env` or environment variable):
```bash
export FILEVYASA_LLM_API_KEY=your-key-here
```

**Settings** (`config/settings.yaml`):
```yaml
llm:
  provider: ollama      # or openai, anthropic
  model: llama3.2
  api_base: http://localhost:11434
```

## API Overview

### Folders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/folders` | Add folder to monitor |
| GET | `/api/folders` | List monitored folders |
| POST | `/api/folders/{id}/sync` | Re-sync folder |
| DELETE | `/api/folders/{id}` | Remove folder |

### Files
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/files/` | List files (with filtering) |
| GET | `/api/files/{id}` | Get file details |
| GET | `/api/files/categories/stats` | Category statistics |

### Config
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config/` | Get current settings |
| POST | `/api/config/llm` | Update LLM settings |
| GET | `/api/config/supported-extensions` | List supported types |

## Architecture

```
filevyasa/
├── api/           # FastAPI routes
├── db/            # SQLite persistence
├── extractor/     # Content extractors by file type
├── llm/           # Summarizer, ImageDescriber
├── scanner/       # Directory scanning
├── sync/          # Folder sync orchestration
└── models/        # Pydantic schemas
```

### Extractors

Each file type has a dedicated extractor:
- **TextExtractor** — Plain text, markdown
- **PDFExtractor** — PDF with OCR fallback
- **OfficeExtractor** — DOCX, XLSX, PPTX
- **ImageExtractor** — EXIF metadata extraction
- **MediaExtractor** — Audio/video metadata, Whisper transcription
- **NotebookExtractor** — Jupyter notebooks
- **CodeExtractor** — Source code files (metadata only)

## Development

```bash
# Install with dev dependencies
uv sync --dev

# Run linter
uv run ruff check .

# Run tests
uv run pytest tests/ -v
```
