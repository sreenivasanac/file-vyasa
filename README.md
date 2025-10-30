# FileVyasa — AI-Powered Local File Organizer

## Vision
FileVyasa is a desktop assistant that understands local files, proposes intelligent folder hierarchies, and executes safe move/rename operations with transparent human oversight. The core philosophy: organise your filesystem as effortlessly as having a conversation with an informed librarian.

## V1 Snapshot — Guided Planning
- Tauri-based desktop UI driving a Python/Agno agent backend.
- Single-root scans with content-aware extraction (documents, images, PDFs) and Constella-powered clustering.
- Review-first workflow: suggested moves, rename hints, and duplicate flags appear in a planning board before any action runs.
- Safe executor maintains rollback metadata for every approved operation; no deletions or unattended automation.
- BYOK remote LLM support for summaries and naming; local-only mode relies on heuristics.

## V2 Outlook — Personalised Intelligence
- Preference persistence remembers user rules, folder policies, and naming conventions across sessions.
- Hybrid model routing enables switching between remote providers and local Ollama models per task.
- Enhanced planning heuristics balance whole-folder moves vs per-file adjustments, complemented by cluster mini-maps and bulk rename trays.
- Incremental review allows partial approvals, session pause/resume, and enriched duplicate workflows.
- Metrics and audit views surface confidence distributions, action histories, and exportable logs.

## Getting Started (Design Phase)
Implementation has not begun. Review the design plans under `agentic_development_docs/project_design_plan/` for detailed specifications before coding.