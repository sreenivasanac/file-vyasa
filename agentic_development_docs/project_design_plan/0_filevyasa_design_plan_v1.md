# FileVyasa Design Plan — V1

## Product Goal
Deliver a trustworthy, human-in-the-loop desktop assistant that scans a user-selected directory, understands file contents at a high level, and produces an approval-ready re-organization plan without performing any irreversible actions.

## Primary Use Cases
- Triage a single messy folder (e.g., `Downloads`) into a clearer hierarchy via suggested moves.
- Generate concise semantic summaries per file to help the user decide how to file items.
- Apply a handful of user-provided prompts/rules (e.g., "keep invoices under Finance") during planning.

## Feature Scope
### Must Have
- Manual directory selection and scoped crawl (one root per run, depth configurable).
- Extraction pipelines for common document types (text, Markdown, Office docs, PDFs with embedded text) and EXIF metadata for images.
- Constella-powered clustering to suggest 8-10 groups and recommended folder names.
- Folder planning board that lists proposed moves per cluster with confidence badges and rationale snippets.
- Plan approval workflow: user can accept/reject individual actions before any filesystem change is executed.
- Safe executor that only moves or renames files after approval and records rollback metadata ("move", source path, destination path, timestamp) , ("rename", earlier_name, updated_name, file path).
- Duplicate detection via hashing with clear "Mark as duplicate" suggestions (no deletions).
- BYOK remote LLM support (OpenAI-compatible endpoint) for summarisation and naming hints.

### Should Have (Time-Permitting)
- Lightweight rename suggestions for single files based on extracted summaries.
- Basic preference persistence (recent roots, ignored folders, confidence threshold).

### Out of Scope
- Background watchers or scheduled automation.
- Local LLM execution (deferred to V2).
- Complex visualisations (UMAP plots, interactive graphs) beyond tabular cluster summaries.
- Semantic search or smart folders.

## Experience Flow
1. User launches the Tauri desktop app and selects a target folder.
2. Agent runs Scan → Extract → Cluster → Plan workflow, emitting a transparent task checklist.
3. Planning board groups recommendations by proposed destination with confidence color coding.
4. User can expand an item to see justification, override destination, or reject it.
5. After approval, executor runs moves sequentially, showing live status and allowing cancellation.
6. Session summary (actions taken, confidence, rollback token) is saved locally.

## Technical Specification
### Architecture Overview
- **Frontend**: Tauri shell with a Vite/React (TypeScript) UI for the planning board and review modals.
- **Agent Core**: Python 3.11 service orchestrated via Agno, exposed to Tauri through a local HTTP bridge or plugin IPC.
- **Pipelines**: Modular components for scanning, extraction, clustering, planning, and execution, each exposed as Agno tools.

### Module Breakdown
- **Scan Module**: Walks directory within allowlist, collects metadata, honours ignore rules.
- **Extraction Module**: For reading different file formats, for now convert most file format types to markdown format using markitdown library https://github.com/microsoft/markitdown .  Read only first 50 lines of the markdown document. Pass this, along with the filename, metadata to an LLM to give 1. ai_brief_summary (2 lines) and 2. ai_summary (4 lines).
- **Clustering Module**: Converts digests to Constella `ContentUnit`s, runs seeded K-Means, returns cluster labels, artifacts and embedding values.
- **Folder structure Planning Module**: Passes three things to an LLM as a prompt:
   - 1. cluster labels
   - 2. user provided rules and prompts 
   - 3. for each cluster, list of file names and summary of its file contents -> passes these to an LLM to decide folder proposal;
- **File operation Planning module**: computes folder-organization score for whole-folder vs per-file moves - by creating a prompt: containing the ENTIRE folder tree (planned), current folder tree to operate, list of each file names and their corresponding short summary of this folder, and important metadata (file-type, etc) of files in this folder.
- **Approval State Manager**: Stores pending actions, user overrides, and notes until execution.
- **Execution Module**: Performs moves/renames atomically, logs steps, records rollback tokens.

### Agent Workflow
```
scan_root -> extract_content -> constella_cluster -> generate_plan -> await_user_review -> execute_actions -> persist_session_log
```
Workflow orchestrated in Agno with explicit human-in-the-loop gate before `execute_actions`.

### Tooling & Integrations
- Agno MCP tools: `file_ops`, `content_extractors`, `constella_cluster`, `rename_planner`, `duplicate_detector`, `preview_diff` (text-based in V1).
- LiteLLM (or Agno model router) for invoking remote LLM summarisation endpoints.

### Data Persistence
- Lightweight SQLite (via SQLModel) or Parquet file to store session logs, rollback tokens, user preferences.
- Cached embeddings stored on disk alongside session metadata to avoid recomputation within a run.

### UI/UX Requirements
- Single window with three panels: scan summary, suggested folders, selected item detail.
- Action chips for Accept/Reject/Defer, with keyboard shortcuts.
- Confidence indicator colours: Green ≥85%, Yellow 60–84%, Red <60% (red items default to "Needs review").

### Security & Privacy
- No files leave device except optional LLM API calls (respect BYOK endpoints, provide toggle for "local only" summarisation fallback using heuristics).
- Enforce path allowlists; prevent traversal into system directories.
- Store API keys encrypted using Keychain (macOS) with pluggable secret storage for other OSs.

### Observability & Logging
- Local JSONL log per run capturing tool calls, durations, and outcomes.
- Expose condensed log in UI for transparency; enable export for debugging.

### Performance Targets
- Optimise for directories up to 5k files (mixed types) with plan generation under 2 minutes on Apple silicon M-series baseline.
- Use streaming extraction and incremental clustering to avoid high memory usage (>2 GB).

## Technical Requirements
### Runtime & Frameworks
- Python 3.11 runtime (packaged via PyInstaller or uv) for agent backend.
- Node 20 + Tauri CLI for desktop shell and UI bundle.

### Libraries & Services
- Constella (local package import) for clustering.
- PDF/DOC readers: `pdfplumber`, `python-docx`, `markdown-it-py`.
- Image metadata: `Pillow`, `exifread`.
- Hashing/Dedup: `xxhash` or `hashlib` SHA256.
- Config: `pydantic` for schema validation.
- Optional: `liteLLM` for LLM routing.

### Configuration
- App settings file (`settings.json`) storing ignore rules, confidence threshold, preferred models.
- BYOK key entry modal writing to secure storage.
- Allow user to set extraction limits (max file size, skip archives) per run.

### Storage & Filesystem Requirements
- Require read/write permissions for target directories.
- Maintain `.filevyasa/rollback/<timestamp>.json` within user Library/Application Support for undo metadata.

### Testing & Validation
- Unit tests for extraction parsers and planning heuristics (Pytest + Hypothesis for edge cases).
- Integration test harness pointing at sample directories in `sample_data/`.
- Manual QA checklist covering plan review, rejection flow, rollback verification.

### Deployment & Packaging
- Distribute signed macOS universal binary via Tauri bundler.
- Provide CLI flag to run agent backend standalone for automated tests.

## Acceptance Criteria
- User can complete a full plan-review-execute loop without shell access.
- Every executed action has a corresponding rollback entry verified in tests.
- System gracefully handles unsupported files by flagging them for manual review.

## Risks & Mitigations
- **LLM Latency**: Cache intermediate summaries; expose progress indicators to avoid perceived hangs.
- **Misclassification**: Require explicit approval; surface rationale and confidence thresholds.
- **Permissions**: Request elevated permissions only when required; document setup in onboarding flow.

## Open Questions / Follow-ups
- Determine preferred secure storage mechanism for Windows/Linux ahead of cross-platform work.
- Decide whether to bundle a minimal local summariser for offline mode or defer to V2.
