# Agno-driven Agentic Features for FileVyasa

## Why Agno for FileVyasa
- Multi-model support: OpenAI, Anthropic, Groq, Ollama, OpenRouter, Bedrock, etc., through Agno model adapters, enabling BYOK remote keys plus local LLMs in one interface.
- First-class tools and MCP: Structured tool orchestration, async retries, caching, and MCP endpoints to expose filesystem, EXIF, Constella, and preview tools safely.
- Human-in-the-loop primitives: Built-in run pausing, approval hooks, guardrails, and session state align with FileVyasa’s review-before-apply workflow.
- Observability: Session history, metrics, and telemetry provide review queues, logs, and rollback context.

## Immediate Features (V1–V3)
### 1. Tooling via MCP and Agno Toolkits
- Expose local capabilities as MCP servers or native tools:
  - `file_ops`: read, stat, move, copy (no delete), conflict resolver, rollback logger.
  - `content_extractors`: PDF/DOCX/text/image OCR, EXIF readers.
  - `constella_cluster`: build `ContentUnit`s, embed, cluster, return labels and cohesion metrics.
  - `rename_planner`: propose semantic filenames with reasons and confidence.
  - `duplicate_detector`: hash and near-duplicate checks.
  - `archive_peek`: safe list/peek into archives.
  - `preview_diff`: render dry-run plan and confidence badges for UI review.
- Use Agno MCP tool selection filters and tool-call limits to sandbox behavior.

### 2. Human-in-the-loop Gates
- Pre-hooks/post-hooks pause at Plan → Propose → Review → Execute checkpoints.
- Encrypted assets: prompt for passwords; accept user-provided summaries when declined.
- Confidence thresholds: require approval under 85%; auto-apply only above configured confidence.

### 3. Agent Memory and Preferences
- Agno Memory stores approved folder templates, naming conventions, ignored paths, merge/suppress cluster decisions, and confidence thresholds.
- Session summaries keep long chats concise while retaining preferences.

### 4. Knowledge Base for Rules/Prompts
- Agno Knowledge hosts reusable prompts/rules (invoice patterns, project taxonomies) with hybrid search to fetch relevant instructions per task.

### 5. Model Routing and Cost Controls
- Configure backend per capability (local small model for tagging, remote stronger model for rename planning).

### 6. Workflows for Dry-run to Apply
- Workflow steps: scan → extract → cluster → plan → review → execute → log.
- Conditional/router steps decide whole-folder vs per-file actions using folder-organization score.

### 7. Guardrails and Safety
- Prompt-injection and PII guardrails on user rules; moderation checks on free-form prompts.
- Tool sandboxing: no delete commands, path allowlists, filename sanitisation.

### 8. Observability and Logs
- Agno metrics/telemetry and session records render tool calls, cost/time per step, success/failure, and run IDs to map into rollback UI.
 - Logging & Observability (move from later to baseline minimal)
 •  Minimal local activity log from day one (path, action, time, confidence, txid); richer timeline view can remain V4.

### 9. Whole‑Folder Move Heuristics (clarify existing section)
 •  Include cohesion of filenames, subtree topic variance, shared EXIF/date ranges, and presence of project markers (.git, package.json) to decide atomic moves. Always preview with override controls.

## 10. Move-Folder-as-a-Unit Logic
- Compute folder-organization score (tree layout consistency, intra-folder topic cohesion, naming patterns, recency).
- Router workflow step: scores above threshold propose whole-folder relocation; otherwise expand into per-file actions, always with preview and confirmation.

## Later Versions (V4+)
### 1. Teams and Specialized Agents
- Planner/executor split: planner handles clustering/structure, executor agents process batches in parallel.
- Watcher agent monitors Smart Folders and triggers plans when new files arrive.

### 2. Advanced Knowledge and RAG
- Semantic search (“find client payment terms”) with agentic chunking and hybrid retrieval for rename exemplars.

### 3. Scheduling and Queues
- Batch scheduler with retries/backoff for large trees; resumable runs after failure.

### 4. Multimodal Pipelines
- Image/video descriptors via Agno model adapters enrich clustering and rename suggestions.

### 5. Control Plane and AgentUI
- Optional AgentOS API exposure; connect to AgentUI for a ready-made chat/session browser alongside desktop UI.


### 6. File Type Coverage (add a few)
 - Images: .raw/.cr2/.nef; Audio: .flac/.ogg; Video: .wmv/.mts; Text:
    .pages/.numbers; Archives: .7z/.rar.

### 7. Constella Integration (tighten)
 •  Explicit mapping: ContentUnit fields = {file_name, summary, keywords, mime, exif, parent_path, size, created_at}.
 •  Cluster selection: silhouette/elbow/Davies–Bouldin already listed; add
    min_cluster_size and outlier bucket; expose UMAP preview toggle.
 •  Folder suggestion rules: cluster→proposed-folder name via top keywords +
    exemplar; allow merge/split in UI.

### 8. Conflict policy
  - Conflict policy presets: {keep_new, keep_old, append_counter, append_datetime}; user‑selectable default. Protected paths/symlinks: never traverse system dirs; detect and avoid symlinks/junction loops; atomic moves.

 ### 9. Policy & Templates (expand Agent Tooling and Core Capabilities)
 •  Folder policies: never‑move paths, treat‑as‑atomic folders, whole‑folder vs per‑file heuristics tunables.
  - De‑duplication actions: report only, move to Duplicates/, replace with
    hardlink/symlink (opt‑in).

 11) Tooling Additions (extend Agent Tooling list)
 •  Filesystem watcher for Smart Folders; Transaction log store with reversible ops;
    Path normalizer/cross‑platform sanitizer; EXIF/metadata writers (for rename syncing where safe).
 •  Password broker (prompt/cache per session) and Archive peeker (list entrieswithout extract).

Memory of corrections scoped by directory profile; show why a suggestion was made (e.g., “due to EXIF date + Constella cluster 3”).



## File-Type Coverage Targets
- Images: `png`, `jpg`, `jpeg`, `gif`, `bmp`, `tiff`, `webp`, `heic`.
- Text/Docs: `txt`, `md`, `rtf`, `odt`, `doc`, `docx`.
- Spreadsheets: `xls`, `xlsx`, `ods`, `csv`.
- Presentations: `ppt`, `pptx`, `key`, `odp`.
- PDFs: `pdf` (OCR enhancements later).
- Video/Audio: `mp4`, `mov`, `avi`, `mkv`, `webm`, `m4v`, `mp3`, `wav`, `m4a`, `flac`.
- Archives: `zip`, `tar`, `gz`, `rar`, `7z`.

## Illustrative Agno Config Snippet
```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from agno.os import AgentOS

file_tools = MCPTools(servers=[
    {"transport": "stdio", "command": "file_ops_server"},
    {"transport": "stdio", "command": "constella_server"},
    {"transport": "stdio", "command": "extractors_server"},
])

organizer = Agent(
    id="file-organizer",
    name="File Organizer",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[file_tools],
    instructions=["Plan → propose → wait for approval before mutations"],
    add_history_to_context=True,
    markdown=True,
)

agent_os = AgentOS(agents=[organizer])
app = agent_os.get_app()
```

## Sortio-inspired UI Hooks via Agno
- Review queue with confidence badges maps to Agno tool-call telemetry per step.
- Multi-select Apply/Cancel feeds workflow execute step with selected subset only.
- Inline previews use `preview_diff` tool outputs attached to session history.
