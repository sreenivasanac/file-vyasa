# FileVyasa — AI-Powered Local File Organizer

A desktop application that scans local directories, extracts content from files, and uses AI to generate summaries, describe images, and transcribe media—helping you understand and organize your filesystem.

## Features

- **Smart Folder Monitoring** — Add folders to monitor, auto-detect changes on re-sync
- **Content Extraction** — Supports 30+ file types including documents, images, media, code, and archives
- **AI Summarization** — Generate concise summaries for documents using local (Ollama) or cloud LLMs
- **Image Description** — AI-powered descriptions for photos and images
- **Media Transcription** — Audio/video transcription via Whisper
- **Desktop App** — Native cross-platform app with file browser, search, and filtering

## Project Structure

```
file-vyasa/
├── backend/          # Python FastAPI backend
├── frontend/         # Tauri + React desktop app
├── agentic_development_docs/  # Design docs and roadmap
└── sample_data/      # Test data for development
```

## Quick Start

### Prerequisites
- Python 3.11+ with [uv](https://github.com/astral-sh/uv)
- Node.js 18+ with pnpm
- Rust (for Tauri desktop app)
- [Ollama](https://ollama.ai) (recommended for local AI) or cloud LLM API key

### Running

**Backend:**
```bash
cd backend
uv sync
uv run python run.py
```

**Frontend:**
```bash
cd frontend
pnpm install
pnpm tauri:dev
```

Both services must run concurrently. The frontend connects to the backend at `http://127.0.0.1:8000`.

## LLM Configuration

### Ollama (Local, Recommended)
```bash
ollama pull llama3.2
```
No API key required—runs entirely on your machine.

### OpenAI / Anthropic
```bash
export FILEVYASA_LLM_API_KEY=your-key-here
```

Configure provider/model in the Settings panel or `backend/config/settings.yaml`.

## Supported File Types

| Category | Extensions |
|----------|------------|
| Documents | PDF, DOCX, XLSX, PPTX, TXT, MD, RTF |
| Images | JPG, PNG, GIF, WEBP, HEIC, BMP, TIFF |
| Media | MP3, MP4, WAV, FLAC, M4A, MOV, AVI, MKV |
| Code | PY, JS, TS, HTML, CSS, JSON, YAML, and more |
| Notebooks | IPYNB |
| Archives | ZIP, TAR, GZ (metadata only) |

## Documentation

- [Backend README](backend/README.md) — API endpoints, configuration, development
- [Frontend README](frontend/README.md) — UI architecture, building, development