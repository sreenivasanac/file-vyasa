# FileVyasa — AI-Powered Local File Organizer (Initial Plan)

## 1. Purpose and Vision
FileVyasa is a personal AI assistant that scans, understands, and organizes local files. It proposes clear folder hierarchies, safely moves or renames file items. It supports both remote LLMs (BYOK -> OpenAI, Grok etc) and local models (e.g., Ollama).

Core philosophy: make finding and organizing files as effortless as conversing with an intelligent librarian who knows your work.

## 2. Problem It Solves
If your Desktop, Downloads, or Documents are cluttered, FileVyasa automates the tedious sorting and renaming work. By analyzing meaningful content and context—not just file extensions—it ensures everything ends up where it logically belongs.

## 3. How It Works
- **Scan & understand**: read file contents, metadata, and EXIF (for media), plus contextual cues.
- **Cluster insights**: generate high-level visualisations of related files via Constella’s seeded K-Means workflow so proposed folders reflect real content themes.
- **Plan**: propose a folder structure and per-file actions in an interactive “folder planning mode.”
- **Review & approve**: you stay in control—approve, reject, or adjust rules/prompts before any action. The agent communicates its thoughts, plans, and actions clearly to the user.
- **Execute safely**: perform moves/renames with conflict resolution; no deletions.
- **Learn from feedback**: remember corrections, preferences, rules, and prompts to improve.

### Folder Move Decision Logic
- **Signals analysed**: folder tree layout, naming consistency, shared metadata (dates, authors), per-file content summaries, duplication ratio, and recent activity.
- **Scoring**: compute a folder-organization score (cohesion of file descriptors, topic variance, nesting depth). Scores above a threshold trigger “move-as-a-unit” recommendations; lower scores surface per-file actions.
- **Decision flow**: simulate moves in a dry-run preview, highlight affected paths, and let users approve whole-folder relocation or drill down to override individual files.
- **Safety**: every queued move stores rollback metadata so folders can be restored if a later review reverses the decision.

### Example Transformation
Before:
```
/home/user/messy_documents/
├── IMG_20230515_140322.jpg
├── IMG_20230516_083045.jpg
├── IMG_20230517_192130.jpg
├── budget_2023.xlsx
├── meeting_notes_05152023.txt
├── project_proposal_draft.docx
├── random_thoughts.txt
├── recipe_chocolate_cake.pdf
├── scan0001.pdf
├── vacation_itinerary.docx
└── work_presentation.pptx

0 directories, 11 files
```

After:
```
/home/user/organized_documents/
├── Financial
│   └── 2023_Budget_Spreadsheet.xlsx
├── Food_and_Recipes
│   └── Chocolate_Cake_Recipe.pdf
├── Meetings_and_Notes
│   └── Team_Meeting_Notes_May_15_2023.txt
├── Personal
│   └── Random_Thoughts_and_Ideas.txt
├── Photos
│   ├── IMG_20230515_140322.jpg
│   ├── IMG_20230516_083045.jpg
│   └── IMG_20230517_192130.jpg
├── Travel
│   └── Summer_Vacation_Itinerary_2023.docx
└── Work
    ├── Project_X_Proposal_Draft.docx
    ├── Quarterly_Sales_Report.pdf
    └── Marketing_Strategy_Presentation.pptx

7 directories, 11 files
```

Reference inspiration: @agentic_development_docs/project_design_plan/sample_product_images/Screenshot 2025-10-30 at 6.36.51 PM.png

## 4. Core Capabilities (Current Scope)
- **Model flexibility**: switch between remote providers (OpenAI, Claude, Grok, etc.) and local models (Ollama).
- **Understanding and classification**:
  - Extract text from PDFs, DOCX, images (via image descriptors), and other formats.
  - Interpret images and tag photos via image-to-text and EXIF metadata.
  - Handle video files via EXIF today, with richer descriptors considered for later versions.
  - Combine file metadata (creation date, size, type) with content analysis.
  - Build clustering maps of files using the Constella library so related files can be grouped intelligently before user review. The visualisation of the file as clusters (in web HTML javascript format) is shown to the user in the UI.
- **Copilot Mode**: chat-style instructions (e.g., “read and rename all PDFs in this folder with this rule Meeting_notes_DD-MM-YY”).
- **Confidence & safety**:
  - Four-level confidence system (e.g., 85% threshold for autonomous actions).
  - Clarifying questions for low confidence; visual indicators like green/yellow/red.
  - Safe operations only: move/rename/copy with conflict resolution; no deletions.
  - Duplicate detection.
- **Agentic experience & control**: the agent explains its reasoning; users can pause, inject rules/prompts, or redirect the plan mid-execution, and every action is reviewable.
- **Configuration**: BYOK for remote AI keys; configure local Ollama endpoints; broadly configurable behaviours via app settings.
- **Platform support**: macOS is the primary target, with Linux and Windows preferred as well.
- **Initial file-type coverage**:
  - Images: .png, .jpg, .jpeg, .gif, .bmp, .tiff, .webp, .heic
  - Text: .txt, .docx, .md, .rtf, .odt
  - Spreadsheets: .xlsx, .csv, .xls, .ods
  - Presentations: .ppt, .pptx, .key, .odp
  - PDFs: .pdf
  - Video: .mp4, .mov, .avi, .mkv
  - Audio (metadata-focused): .mp3, .wav, .m4a
  - Archives (metadata + safe relocation): .zip, .tar, .gz

### Constella Integration
- **Inputs prepared**: each file becomes a Constella `ContentUnit` containing summaries, keyword tags, MIME type, EXIF snippets, and directory context. Embeddings are generated through LiteLLM adapters (Fireworks/OpenAI or configured equivalents).
- **Clustering workflow**: candidate cluster counts are scored with silhouette, elbow, and Davies–Bouldin metrics before a seeded K-Means run assigns clusters with reproducible centroids and inertia diagnostics.
- **Outputs consumed by FileVyasa**: cluster labels, cohesion scores, and exemplar files translate into suggested folder groups and naming hints surfaced inside folder planning mode. Optional UMAP plots power visual previews.
- **User involvement**: users can rename, merge, or suppress Constella-suggested folders before execution; accepted feedback trains preference memory for future runs.

### Agentic UX Flow (Codex/Claude-inspired)
1. **Plan**: assemble a transparent checklist of goals, reasoning snippets, and upcoming tool calls before any mutation.
2. **Propose**: surface actions in a review queue with confidence badges, diffs/previews, and quick filters (whole-folder vs per-file).
3. **Review**: let users tweak prompts/rules inline, approve in bulk, or pause execution mid-stream.
4. **Execute**: show live logs similar to code copilots; users can halt individual steps if something looks wrong.
5. **Learn**: store overrides and corrections so future plans auto-align with the user’s preferences.

### Agent Framework Notes (Agno AI)
- **Baseline integration (main requirements)**:
  - Use Agno’s tool orchestration to sequence file operations, metadata extraction, Constella clustering, and rename planners as discrete tools.
  - Keep human-in-the-loop checkpoints for every plan approval stage.
  - Persist user rules, naming conventions, and folder policies via Agno memory slots.
  - Prompt for encrypted PDFs through Agno MCP; if declined, allow manual summaries that inform classification.
  - Run dry-run simulations using Agno workflows before committing filesystem changes.
- **Later-version enhancements**:
  - Coordinate specialised planner/executor agents for large directories.
  - Enable background watchers that trigger re-organisation when new files arrive.
  - Store richer preference embeddings for adaptive automation.
  - Support retryable long-running tasks using Agno queue backoff for massive batches.

## 5. Agent Tooling
- File operations (read, move)
- Image read (descriptor + metadata extraction)
- Constella-based clustering of file information
- Folder structure planning
- Content extraction pipelines (PDF/DOCX parsers, OCR for images when enabled)
- EXIF and metadata reader for images, audio, and video
- Hash-based duplicate detector (e.g., SHA-256 fingerprints)
- Archive inspector to safely peek into .zip/.tar without full extraction
- Conflict resolver for filename collisions with suggested alternatives
- Undo/rollback logger capturing before/after states
- Rule and prompt library for reusable instructions
- Password prompt interface for protected documents
- Semantic embedder service to back future semantic search
- Batch scheduler for queued or off-peak operations

## 6. Versioned Feature Highlights
### V3 Experience
- In-app preview of planned operations.
- Batch rename suggestions using file contents, current names, metadata, and EXIF; users select subset/all, then Apply or Cancel.
- Reference inspirations:
  - @agentic_development_docs/project_design_plan/sample_product_images/57f935b8-7c46-4146-b733-e53c3bb460d2.avif
  - @agentic_development_docs/project_design_plan/sample_product_images/f86a78a9-004a-4539-a528-aafb4fd0b1bd.avif
  - @agentic_development_docs/project_design_plan/sample_product_images/9df5f947-2fd4-434e-a106-66ca4b5c00ad.avif

### Later Versions (V4 and beyond)
- Semantic search (e.g., “Find client payment terms”) powered by advanced vector search.
- OCR for non-text PDFs (reference: @agentic_development_docs/project_design_plan/sample_product_images/image.png).
- Rollback/undo system for file moves with sample CLI actions:
  - `python easy_rollback_system.py --list`
  - `python easy_rollback_system.py --undo 123`
  - `python easy_rollback_system.py --undo-today`
  - Inspiration asset: @agentic_development_docs/project_design_plan/sample_product_images/image copy 2.png
- Google Drive integration.
- Parallel and batch processing.
- Activity logs showing what happened, when, and where.
- Auto-group / Smart Folder mode:
  - Convert any folder into a Smart Folder that auto-creates relevant subfolders.
  - Automatically sort new files into those subfolders based on observed patterns.
- “Never organize again” vision: a continuously self-organizing folder system.

## 7. Inspiration Assets (Ideas Only)
- @agentic_development_docs/project_design_plan/sample_product_images/Screenshot 2025-10-30 at 6.36.51 PM.png
- @agentic_development_docs/project_design_plan/sample_product_images/Screenshot 2025-10-30 at 6.33.25 PM.png
- @agentic_development_docs/project_design_plan/sample_product_images/c8f5a808-35f7-4dd9-a1f8-2098caa0bfcc.avif
- @agentic_development_docs/project_design_plan/sample_product_images/658c9ee7-1925-43e1-b57c-6b058951789b.avif
- @agentic_development_docs/project_design_plan/sample_product_images/57049b68-f829-4e24-a88d-93b4afd508c5.avif
- @agentic_development_docs/project_design_plan/sample_product_images/image.png
- @agentic_development_docs/project_design_plan/sample_product_images/sortio

### Inspiration Notes (Sortio)
- Multi-select Apply/Cancel trays shown in Sortio references inspire the selection UX for rename/move batches.
- Confidence badges beside each planned action echo competitor patterns and help users gauge trust quickly.
- Inline preview panes (documents, thumbnails) keep context visible during approval.

### Inspiration Notes (General Competitors)
- Incorporate relevant motifs from the broader reference set—review queues, visual confidence indicators, and timeline logs—while tailoring the interaction model to FileVyasa rather than replicating external UIs.

## 8. Additional Notes & Guardrails
- Strong guardrails against deleting files: moves/renames/copies only.
- Some folders remain intact when already reasonably organized; the agent considers folder trees, content summaries/descriptors, and names to decide whether to move entire folders or individual files.
