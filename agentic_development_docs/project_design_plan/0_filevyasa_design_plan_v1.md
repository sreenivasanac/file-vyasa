# FileVyasa Design Plan — V1 (Stepwise: v1.1–v1.5)

## Overall Product Goal (V1 Series)
Deliver a trustworthy, human-in-the-loop desktop assistant that scans a user-selected directory, understands file contents at a high level, and produces an approval-ready re-organization plan without performing any irreversible actions.

Primary scope for V1. x: single-folder triage on macOS with basic planning UI and safe execution. Advanced personalisation, caching, heavy optimisation, and smart modes are deferred to V2+ (see `0_filevyasa_design_plan_v2.md`).

---

## V1.1 — Minimal End‑to‑End Slice (Scan → Summarise → Simple Suggestions)

### Product Goal (v1.1)
Allow the user to select a single folder, run basic content-aware extraction for common files, and show per-file summaries.

### Feature Scope (v1.1)
- Manual directory selection from the desktop UI (single root only), UI loosely inspired by `sample_product_images/magic/magic_organize_folder.png`.
- Extraction pipelines for common document types (text, Markdown, Office docs, PDFs with embedded text) and EXIF metadata for images.
- For each supported file:
  - Convert to Markdown using `markitdown` where possible.
  - Fill an internal file object with relevant attributes and metadata.
  - For sample of file object class to take inspiration from (another project): /Users/sreenivasanac/SoftwareProjects/brahmasumm2/core/document/base.py

These are the filetypes / mimetypes that we may need to handle:

Users/sreenivasanac/SoftwareProjects/file-vyasa/2_extension_count_downloads.txt 

/Users/sreenivasanac/SoftwareProjects/file-vyasa/2_extension_count_downloads.txt

/Users/sreenivasanac/SoftwareProjects/file-vyasa/3_extension_count_google_drive_1.txt

You can use this sample_data folder as a sample folder to test or as a sample to have an idea:
/Users/sreenivasanac/SoftwareProjects/file-vyasa/sample_data

  - Read only the first 50 lines of the Markdown.
  - Call BYOK remote LLM via LiteLLM (OpenAI-compatible endpoint) with filename + file metadata + snfile content snippet to produce:
    - `ai_brief_summary` (≈2 lines).
    - `ai_summary` (≈4 lines).
- BYOK remote LLM support (through LiteLLM) for summarisation only; no local model routing yet.

### Experience Flow (v1.1)
1. User launches the Tauri desktop app and selects a single target folder.
2. Backend scans the folder within an allowlist, collects basic metadata, and runs extraction + summarisation.
3. UI shows a simple table/list of files with type, size, and brief summary.
4. No moves or rename suggestions yet.

### Technical Scope (v1.1)
- **Frontend**: Tauri shell with Vite + React (TypeScript) SPA for folder picker and basic file list.
- **Agent Core**: Python 3.11 service via Agno, reachable from Tauri through local HTTP or IPC bridge.
- **Modules Implemented** (initial versions):
  - Scan Module (directory walk + ignore rules).
  - Extraction Module using `markitdown` + EXIF readers.
  - LLM Summariser + simple rename-hint generator.
- **Tooling & Integrations** (minimal):
  - Agno tools: `file_ops` (read-only), `content_extractors`.
  - Remote LLM only (OpenAI-compatible) via LiteLLM; keys read via BYOK configuration.
- **Persistence (v1.1)**: lightweight SQLite database to store scanned file objects and summaries for the current run (single-root only); session logs optional.

---

## V1.2 — Basic File Objects, Attributes, and In-App Preview

### Product Goal (v1.2)
Evolve from raw summaries to structured file objects and a slightly richer UI so the user can inspect a single file’s details (metadata, summaries) without yet introducing clustering or rename suggestions.

### Feature Scope (v1.2)
- Formalise a `FileObject` schema (language-agnostic design) capturing:
  - Path, filename, extension, MIME.
  - Size, created/modified timestamps.
  - Basic EXIF/metadata for images. (Think what other file related metadata need to be saved)
  - `ai_brief_summary` and `ai_summary` (no rename field yet).
- Backend returns a list of `FileObject`s for the scanned folder, backed by SQLite storage.
- UI enhancements:
  - Expandable file detail panel (right or bottom) to inspect a single file.
  - Basic filters (e.g., by type) and search-by-name within the list.
- Store recent root folders and simple ignore rules in SQLite (no full preference/profile system yet).

### Experience Flow (v1.2)
1. User runs the same scan as v1.1.
2. Results populate a structured table of `FileObject`s.
3. Clicking a row opens a detail view with metadata and AI summaries.
4. User can refine which files to focus on via simple filters.

### Technical Scope (v1.2)
- Extend the Scan + Extraction Module to always populate `FileObject`s consistently and persist them in SQLite.
- Store recent roots, ignored patterns, and last-used model endpoint in SQLite instead of JSON.
- Wire UI state to `FileObject` schema and detail view; still no clustering or move/rename execution.

---

## V1.3 — Clustering & Folder Planning Board (Preview Only)

### Product Goal (v1.3)
Introduce Constella-powered clustering and a first version of the folder planning board, but keep the system in "preview only" mode: no filesystem mutations yet.

### Feature Scope (v1.3)
- Constella-powered clustering to suggest ~8–10 groups and tentative cluster names as candidates for folder names.
- Convert `FileObject`s into Constella `ContentUnit`s using summaries + metadata.
- Folder planning board UI that lists:
  - Proposed clusters as candidate folders.
  - Files under each cluster with confidence indicators.
  - Basic ability to rename cluster labels (proposed folder names) in the UI.
- Planning workflow remains preview-only:
  - Show "Planned destination" per file.
  - No actual move/rename is executed yet.

### Experience Flow (v1.3)
1. After scan and summarisation, user clicks "Generate Plan".
2. Backend runs Constella clustering and returns cluster labels and assignments.
Update file with the following attributes:
- cluster_id: Optional[str] - Assigned Constella cluster
- cluster_confidence: Optional[float] - Confidence score for cluster assignment
- ai_suggested_folder: Optional[str] - LLM-suggested destination folder
- ai_suggested_filename: Optional[str] - LLM-suggested rename
- ai_keywords: list[str] - Extracted keywords/tags
- embedding_vector: Optional[list[float]] - For semantic search (v4+)

3. Planning board groups files by cluster with proposed folder names.
4. User can review clusters and adjust proposed folder names, but cannot yet apply changes.

### Technical Scope (v1.3)
- Implement **Clustering Module**:
  - Use Constella library from `/Users/sreenivasanac/SoftwareProjects/constella`.
  - Generate embeddings via configured LLM endpoint.
  - Return cluster IDs, names, and cohesion scores.
- Implement **Folder Planning Module (Preview)**:
  - Use cluster labels + user-provided high-level rules/prompts + summaries/metadata to derive proposed folder names (via LLM prompt).
  - No file-operation scores yet; just destination suggestions.
- UI: introduce three-panel layout (scan summary, suggested folders/clusters, selected item detail) aligned with overall vision, but interactions stay simple.
---

## V1.4 — Action Planning & Approval State (Still No Execution)

### Product Goal (v1.4)
Move from high-level cluster preview to explicit per-file action planning ("move from → to", "rename →"), and introduce an approval state manager, while still not touching the filesystem.

### Feature Scope (v1.4)
- **File Operation Planning Module** (planning only):
  - For each file, compute a proposed action (e.g., move to cluster folder, optional rename suggestion) using:
    - Planned folder tree (based on clusters).
    - Current folder tree.
    - Per-file summaries and metadata.
  - Compute a simple folder-organisation score for whole-folder vs per-file moves via LLM prompt.
- **Approval State Manager (planning only)**:
  - Store planned actions (move/rename) with status: pending/accepted/rejected.
  - Allow user overrides (change destination folder, edit target name) in memory.
- UI:
  - Show a queue/list of proposed actions with confidence colours (green/yellow/red based on simple thresholds).
  - Enable Accept/Reject per action; persist decisions in the in-memory approval state.

### Experience Flow (v1.4)
1. User generates a plan (as in v1.3).
2. Backend derives explicit per-file actions and their confidences.
3. Planning board now shows proposed actions with Accept/Reject controls.
4. User can fully "approve" a plan conceptually, but no actual moves/renames run.

### Technical Scope (v1.4)
- Flesh out **File Operation Planning Module** prompt structure and internal representations for actions.
- Implement **Approval State Manager** in the backend service layer.
- Extend UI to show and edit action details while keeping the filesystem untouched.

---

## V1.5 — Safe Executor, Rollback Metadata, and Duplicates

### Product Goal (v1.5)
Complete the V1 experience loop by adding a safe executor that applies only user-approved actions, records rollback data, and introduces basic duplicate detection.

### Feature Scope (v1.5)
- **Plan Approval Workflow**: user can accept/reject individual actions before any filesystem change is executed.
- **Safe Execution Module**:
  - Execute only approved move/rename actions.
  - Record rollback metadata for every operation, e.g.:
    - `{"type": "move", "source": ..., "destination": ..., "timestamp": ...}`
    - `{"type": "rename", "path": ..., "old_name": ..., "new_name": ..., "timestamp": ...}`
  - Enforce "no delete" safety guardrails.
- **Duplicate Detection via Hashing**:
  - Hash files (e.g., SHA-256) and detect duplicates.
  - Surface "Mark as duplicate" suggestions in the planning board (no automatic delete).
- **Session Summary**:
  - After execution, save a local session summary with actions taken, confidence distribution, and rollback token/location.

### Experience Flow (v1.5)
1. User reviews all proposed actions in the planning board.
2. Once satisfied, user clicks "Apply approved actions".
3. Executor runs moves/renames sequentially with live status and ability to cancel further actions.
4. On completion, user can view a simple session summary and location of rollback data.

### Technical Scope (v1.5)
- Implement **Execution Module** with atomic move/rename operations and error handling.
- Persist rollback metadata under a `.filevyasa/rollback/<timestamp>.json` directory within the appropriate app data path.
- Implement basic **Duplicate Detector** using hashing and integrate suggestions into the planning board.
- Ensure observability: append execution steps to a local JSONL log per run.

---
