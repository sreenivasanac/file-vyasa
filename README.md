# FileVyasa — AI-Powered Local File Organizer

A desktop application that scans local directories, extracts content from files, and generates AI-powered summaries to help you organize your filesystem.

## Project Structure

```
file-vyasa/
├── backend/          # Python FastAPI backend (scanning, extraction, LLM summarization)
├── frontend/         # Tauri + React desktop app
├── agentic_development_docs/  # Design plans and documentation
├── handle_file_types/         # File type analysis utilities
└── sample_data/      # Test data for development
```

## Current Status (v1.1 / v1.2)

- Directory scanning with file discovery
- Content extraction (text, documents, images, PDFs)
- AI-powered file summarization via LiteLLM (Ollama, OpenAI, Anthropic)
- Desktop UI with file list, tree view, filtering, search, and detail views
- SQLite persistence for scan sessions

## Quick Start

### Prerequisites
- Python 3.11+ with [uv](https://github.com/astral-sh/uv)
- Node.js 18+ with pnpm
- [Ollama](https://ollama.ai) (recommended) or cloud LLM API key

### Backend
```bash
cd backend
uv sync
uv run python run.py
```

### Frontend
```bash
cd frontend
pnpm install
pnpm tauri:dev
```

Both services must run concurrently — the frontend connects to the backend API at `http://127.0.0.1:8000`.

## LLM Configuration

FileVyasa supports multiple LLM providers for generating file summaries.

### Ollama (Local, Recommended)

No API key required. Runs entirely on your machine.

```bash
# Install Ollama from https://ollama.ai
# Pull a model
ollama pull llama3.2
```

Default configuration in `backend/config/settings.yaml`:
```yaml
llm:
  provider: ollama
  model: llama3.2
  api_base: http://localhost:11434
```

**Recommended models:** `llama3.2`, `llama3.1`, `mistral`, `phi3`, `gemma2`

### OpenAI / Anthropic

Set your API key as environment variable:
```bash
export FILEVYASA_LLM_API_KEY=your-key-here
```

Then configure in Settings or `settings.yaml`:
```yaml
llm:
  provider: openai  # or anthropic
  model: gpt-4o-mini  # or claude-3-5-sonnet-20241022
```

## Future Plans

See design documents in `agentic_development_docs/project_design_plan/` for V2 roadmap including preference persistence, hybrid model routing, and enhanced organization workflows.