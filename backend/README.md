# FileVyasa Backend

AI-Powered Local File Organizer - Python Backend Service

## Overview

This is the backend service for FileVyasa, providing:
- Directory scanning and file discovery
- Content extraction (text, documents, images)
- AI-powered file summarization via LiteLLM
- RESTful API for frontend integration
- SQLite-based persistence

## Quick Start

### Setup

```bash
# Create virtual environment and install dependencies
uv venv .venv
uv pip install -e ".[dev]"

# Copy environment template and add your API key
cp .env.example .env
# Edit .env with your LLM API key
```

### Configuration

**Secrets** (`.env` file - keep private):
```
FILEVYASA_LLM_API_KEY=your-openai-api-key
```

**Non-secret settings** (`config/settings.yaml`):
```yaml
app:
  debug: false
api:
  host: 127.0.0.1
  port: 8000
llm:
  provider: openai
  model: gpt-4o-mini
```

Environment variables override YAML settings when set.

### Running

```bash
# Run the server
uv run python run.py

# Or using the module
uv run python -m filevyasa
```

The API will be available at `http://127.0.0.1:8000`.

### API Documentation

Once running, visit:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API Endpoints

### Scan Operations

- `POST /api/scan/start` - Start scanning a directory
- `GET /api/scan/{scan_id}/status` - Get scan status and results
- `GET /api/scan/recent` - List recent scans

### File Operations

- `GET /api/files/` - List files with filtering
- `GET /api/files/{file_id}` - Get file details
- `GET /api/files/categories/stats` - Get category statistics
- `GET /api/files/extensions/stats` - Get extension statistics

### Configuration

- `GET /api/config/` - Get current configuration
- `POST /api/config/llm` - Update LLM settings
- `GET /api/config/supported-extensions` - List supported file types

## Testing

```bash
uv run pytest tests/ -v
```

## Project Structure

```
backend/
├── filevyasa/
│   ├── api/           # FastAPI routes and app
│   ├── db/            # SQLite database layer
│   ├── extractor/     # Content extraction modules
│   ├── llm/           # LLM summarization
│   ├── models/        # Pydantic models
│   ├── scanner/       # Directory scanning
│   └── config.py      # Settings management
├── tests/             # Test suite
├── pyproject.toml     # Project configuration
└── run.py             # Server entry point
```

## Version

- v1.1: Basic scan, extraction, and summarization
- v1.2: FileObject schema, SQLite persistence, filtering
