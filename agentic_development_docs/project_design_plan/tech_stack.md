# FileVyasa Tech Stack

## Core Runtime & Frameworks
- **Backend**: Python 3.11 (or newer LTS) orchestrated via Agno agent framework.
- **Frontend**: Tauri desktop shell with Vite + React (TypeScript) SPA UI.
- **Agent Orchestration**: Agno MCP tools, LiteLLM router for multi-model access (OpenAI, Anthropic, Gemini, Ollama).

## AI & Data Processing
- **Clustering**: Constella library (local dependency) for seeded K-Means (or DBSCAN), embeddings, and cluster scoring.
- **LLM/Embedding Clients**: LiteLLM, Ollama HTTP API, SentenceTransformers (V3+), CLIP/LAION models (V4).
- **Document Parsing**: `pdfplumber`, `python-docx`, `markdown-it-py`, `rtf-parser`, `openpyxl`, `python-pptx`.
- **Media Metadata & Previews**: `Pillow`, `exifread`, `ffmpeg`/`ffmpeg-python`, `opencv-python`, `imagehash`.
- **OCR (V4)**: `ocrmypdf`

## Persistence & Configuration
- **Local Stores**: SQLite for session logs and preferences;
- **Vector Index (V3+)**: FAISS or Chroma for knowledge base; Qdrant/Weaviate for semantic search (V4).
- **Config Management**: Pydantic schemas, YAML/JSON config files, OS keychain integration for secrets.
- **Rollback Ledger**: JSONL or SQLite-backed append-only store with optional ZFS/object storage snapshots (V4).

## Platform Services
- **Event Streaming**: Tauri event system as primary bridge between backend and UI; WebSockets from Python backend only if higher-throughput streaming is needed later.
- **Background Tasks**: AsyncIO + uvloop (V2+), Dramatiq/RQ/Temporal for scheduled workflows (V3+/V4).
- **File Watchers (V4)**: Watchdog with platform-specific backends (FSEvents, inotify, USN Journal).
- **Cloud Connectors (V1)**: Google Drive API (`google-api-python-client`, `google-auth`).

## Testing & Tooling
- **Test Frameworks**: Pytest, Hypothesis, Playwright (for Tauri UI smoke tests).
- **Packaging**: Tauri bundler for macOS, Windows, Linux; PyInstaller/uv for backend helpers.
- **Observability**: Structured logging via `structlog`/`loguru`, Prometheus exporter (V4), Grafana dashboards.

## Frontend Libraries
- React Query/RTK Query for data fetching (V2+), XState for workflow state machines (V3+), Tailwind or CSS Modules for styling.
- Data visualisation: Recharts or Victory for metrics; embedded SVG previews from backend.

## CLI & Automation
- Python CLI utilities packaged with Typer/Click for rollback and diagnostics.
- Optional Bash scripts for local developer tooling (linting, packaging).

## Security & Compliance
- Keytar (Tauri) for secrets; TLS/mTLS for service communication (V4).
- Policy engine powered by YAML DSL evaluated via Pydantic/attrs (V4).

