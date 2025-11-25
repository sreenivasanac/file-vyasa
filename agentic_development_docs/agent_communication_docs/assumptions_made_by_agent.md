# Assumptions Made During Implementation

## Architecture Decisions

1. **HTTP API over IPC**: Used FastAPI HTTP localhost API as requested, rather than Tauri IPC. This makes the backend independently testable and potentially usable by other frontends.

2. **Synchronous DB Operations**: Used synchronous SQLAlchemy sessions in API routes for simplicity. Background tasks handle heavy processing.

3. **Background Scan Processing**: Scans run in FastAPI BackgroundTasks to avoid blocking the API. Status polling via `/api/scan/{id}/status`.

4. **Single Process**: No separate worker process or queue system for v1. Background tasks run in the same process.

## Data Model Decisions

1. **FileObject vs FileObjectTable**: Separate Pydantic models for API/logic and SQLAlchemy models for persistence. This allows flexibility in schema evolution.

2. **Category Enum**: Created a fixed set of file categories based on common use cases from the extension count files. Can be extended.

3. **Metadata Storage**: Used JSON columns for flexible metadata storage (`exif_data`, `file_metadata`).

4. **Renamed `metadata` to `file_metadata`**: SQLAlchemy reserves `metadata` as a class attribute, so renamed to avoid conflict.

## Extraction Decisions

1. **Markitdown Primary**: Using `markitdown` as the primary extraction library with fallbacks to `pdfplumber` and `python-docx`.

2. **Content Truncation**: Default 50 lines for content preview to limit token usage in LLM calls.

3. **EXIF via exifread**: Using `exifread` library for broad EXIF support across image formats.

## LLM Integration

1. **LiteLLM for Flexibility**: Using LiteLLM to support multiple providers (OpenAI, Anthropic, etc.) through a single interface.

2. **JSON Response Format**: Requesting structured JSON from LLM for reliable parsing of summaries.

3. **Temperature 0.3**: Low temperature for more consistent, factual summaries.

## File Type Support

1. **Priority Extensions**: Focused on the most common extensions from the provided extension count files (PDF: 183, MP4: 145, JPEG: 93, PNG: 25, etc.)

2. **Code Files as Text**: Treating code files as text for content extraction (may want syntax-aware handling later).

3. **Video/Audio Metadata Only**: Not extracting video/audio content in v1 (would need transcription services).

## Frontend Decisions (v1.1/v1.2)

1. **Tauri 2.x**: Using latest Tauri 2.x with dialog plugin for native folder selection. Cross-platform compatible (macOS, Windows, Linux).

2. **Dark Theme Only**: Implemented dark theme inspired by competitor apps (Sortio, Magic Organize). Light theme can be added later.

3. **Tailwind CSS v4**: Using latest Tailwind v4 with `@tailwindcss/vite` plugin and custom theme variables for consistent styling.

4. **Zustand for State**: Lightweight state management with Zustand instead of Redux. Simpler API, less boilerplate.

5. **TanStack Query**: Using React Query for API data fetching with caching, background refetching, and automatic polling during scans.

6. **Radix UI Primitives**: Using unstyled Radix components (Select, Dialog, Tabs) for accessibility compliance.

7. **Backend Health Check**: Frontend polls `/health` endpoint every 5 seconds to show backend connection status.

8. **API Base URL Hardcoded**: Backend URL `http://127.0.0.1:8000/api` is hardcoded. Should be made configurable for production.

9. **Three-Panel Layout**: Designed layout with sidebar, main content, and detail panel to support future features (clustering, planning board in v1.3+).
