# FileVyasa Design Plan — V3

## Product Goal
Transform FileVyasa into a highly interactive copilot with rich previews, guided batch operations, and semi-automated workflows while keeping robust human control and transparency.

## Strategic Themes
- **Preview Everything**: give users granular visibility into the impact of rename/move actions before execution.
- **Guided Automation**: enable multi-step workflows (rules, templates, batch approvals) with minimal manual intervention.
- **Knowledgeable Assistant**: leverage reusable prompts, knowledge bases, and contextual memory to recommend smarter actions.
- **Operational Insight**: surface advanced logs, metrics, and rollback tools directly in the UI.

## Feature Scope
### Must Have
- Rich preview panes (document snippets, thumbnails, EXIF rolls) embedded beside each proposed action.
- Batch rename tray with multi-select Apply/Cancel controls influenced by Sortio-inspired UI references.
- Rule-based workflow builder: users craft multi-step instructions (e.g., "Move project docs → Rename invoices → Flag duplicates") executed sequentially with checkpoints.
- Knowledge base integration pulling stored prompts/rules based on detected themes (Agno Knowledge + LiteLLM embedding search).
- Advanced duplicate management including near-duplicate detection (perceptual hashing for images, textual similarity for docs) with merge suggestions.
- Expanded activity timeline showing plan stages, approvals, rejections, and execution results.
- Partial auto-apply mode for high-confidence (>90%) actions gated behind user opt-in per session.
- Background resumable tasks: long-running extraction or rename batches can continue while the user reviews completed segments.

### Should Have
- Inline editing of proposed folder names with instant plan recalculation.
- Confidence explanations (why an action is high/low confidence) referencing heuristics and user rules.
- Multi-user workspace concept (share templates/config) for future team support foundation.

### Out of Scope
- Continuous smart folders, semantic search, cloud integrations, OCR for scanned PDFs (pushed to V4).
- Full automation without checkpoints.

## Experience Flow Enhancements
1. User selects a workflow template or builds one via drag-and-drop rule composer.
2. Pipeline runs and streams intermediate previews to UI (documents, audio waveforms metadata, video keyframe thumbnails).
3. Rename tray groups suggestions by confidence; user bulk applies or snoozes groups.
4. Activity timeline records each batch with ability to drill down into plan rationale and preview diffs.
5. After execution, user receives summary with quick links to rollback, share template, or schedule follow-up runs.

## Technical Specification
### Architecture Enhancements
- Introduce event bus (e.g., `asyncio` pub/sub) to stream pipeline events to Tauri frontend via WebSocket bridge.
- Extend visualization service with media preview generators (static thumbnails, waveform PNGs) using ffmpeg/mediainfo.
- Implement workflow builder engine that compiles user-defined recipes into Agno workflows with checkpoints.
- Integrate knowledge base search service using local vector store (FAISS) seeded with stored prompts/templates.

### Module Updates
- **Workflow Compiler**: converts drag-and-drop steps into Agno workflow graph with gating nodes (approval, auto-apply).
- **Preview Generator**: orchestrates document snippet extraction, video keyframes (ffmpeg), audio metadata, and image thumbnails.
- **Confidence Explainer**: surfaces feature weights (cluster cohesion, rule match, historical success) for each action.
- **Timeline Service**: aggregates events into UI-friendly format with filtering by action type, confidence, or outcome.
- **Auto-apply Controller**: enforces thresholds, logs consent, and routes applied actions through fast-path executor.

### Workflow Evolution
```
select_template -> compile_workflow -> stream_events -> generate_previews -> plan_batches -> knowledge_recommendations -> user_review (per batch) -> auto_apply_high_confidence -> execute_batches -> timeline_update -> rollback_index_update
```

### Tooling & Integrations
- New Agno MCP tools: `preview_generator`, `workflow_compiler`, `knowledge_search`, `confidence_explainer`.
- Integrate `faiss` or `chromadb` for local vector store powering knowledge retrieval.
- Extend duplicate detection with `imagehash` and `sentence-transformers`.

### Data & Storage
- Maintain versioned knowledge base entries with metadata (who created, usage frequency).
- Store preview assets in session cache, referenced by timeline events for later viewing.
- Track per-action lineage linking auto-applied operations to their generated evidence (preview, rationale).

### UI/UX Requirements
- Split-pane view: left workflow stages, center action list with inline previews, right detail panel showing rationale and knowledge suggestions.
- Batch controls: "Apply selected", "Snooze", "Ask for clarification" (triggers explanation tool call).
- Timeline tab with vertical progression, filter toggles, and rollback buttons.
- Notification system for completed background tasks.

### Security & Privacy
- Implement content redaction policies for previews (blur sensitive regions unless permitted).
- Provide audit trail export with hashed references to previews (actual files stored locally only).
- Support multi-profile secrets vault (separate BYOK keys per profile) in anticipation of team usage.

### Observability & Logging
- Structured telemetry channel capturing workflow step durations, auto-apply counts, explanation requests.
- Diagnostics panel summarising LLM usage per provider, with per-step token costs.

### Performance Targets
- Stream first previews within 10 seconds for directories >5k files.
- Sustain concurrent review of multiple batches without blocking backend processing (<200 ms latency for UI updates).

## Technical Requirements
### Runtime & Frameworks
- Backend adopts `fastapi`-style async endpoints exposed to Tauri for real-time streaming.
- Introduce `redis` or `sqlite`-backed task queue (e.g., `dramatiq`/`rq`) for background preview generation.
- Frontend uses React state machines (xstate) to model workflow progression and timeline interactions.

### Libraries & Services
- `faiss` or `chromadb` for knowledge vector search.
- `sentence-transformers` for embedding prompts and file summaries.
- `imagehash`, `opencv-python`, `ffmpeg-python` for preview/duplicate work.
- `python-socketio` or `websockets` for event streaming to UI.
- `pydantic` schema upgrades for workflow definitions, ensuring validation before execution.

### Configuration
- Workflow template JSON schema stored under `~/.filevyasa/workflows/` with version control metadata.
- Auto-apply guardrails configurable per template (max actions, confidence threshold, fallback behaviour).
- Preview generation limits (max pages, frame counts) enforced via settings.

### Storage & Filesystem
- Expand `.filevyasa` directory to include `previews/`, `workflows/`, and `timeline/` subfolders with cleanup policies.
- Ensure rollback ledger links to preview assets for contextual undo decisions.

### Testing & Validation
- End-to-end tests simulating workflow templates, including auto-apply paths and explanations.
- Visual regression tests for preview rendering (snapshot comparisons).
- Load testing on event bus to ensure UI responsiveness under high throughput.

### Deployment & Packaging
- Bundle ffmpeg (licence-compliant static binaries) or provide guided installer check.
- Ensure Tauri build signs and notarises additional helper binaries.

## Acceptance Criteria
- Users can preview, approve, or snooze batches with media-rich context.
- Auto-apply actions only execute when confidence ≥ user threshold and are logged with evidence.
- Timeline captures full history and allows instant rollback per action.

## Risks & Mitigations
- **Preview Generation Cost**: Implement caching and rate limits; allow user to disable heavy previews.
- **Knowledge Drift**: Provide review screen for knowledge suggestions; timestamp entries and enable pruning.
- **Background Task Failures**: Add retry policies and surfaced alerts in notifications panel.

## Follow-up Items
- Design semantic search interface leveraging existing knowledge base embeddings (V4).
- Explore collaborative timeline sharing for team environments.
