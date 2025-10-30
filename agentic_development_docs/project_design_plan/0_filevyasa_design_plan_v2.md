# FileVyasa Design Plan — V2

## Product Goal
Elevate FileVyasa from a single-run organiser to a configurable assistant that adapts to user preferences, supports hybrid (remote + local) model execution, and delivers richer planning intelligence while maintaining human supervision.

## Strategic Themes
- **Personalisation**: remember user actions, rules, and folder policies across runs.
- **Model Flexibility**: add local LLM (Ollama) pathways alongside BYOK providers.
- **Deeper Analysis**: enhance clustering with visual context and smarter whole-folder heuristics.
- **Operational Confidence**: expand rollback and audit features without automating execution beyond approvals.

## Feature Scope
### Must Have Enhancements
- Profile persistence storing user rules, ignore paths, naming conventions, and confidence thresholds (encrypted at rest).
- Local LLM integration via Ollama with runtime model selection and cost/latency comparisons.
- Enhanced planning heuristics that evaluate folder-level cohesion versus file-level moves, supported by metrics dashboards.
- Visual mini-maps (static UMAP snapshot) to illustrate cluster relationships within the planning UI.
- Bulk rename tray allowing the user to preview semantic rename suggestions per cluster before approval.
- Incremental planning: ability to accept subsets of actions and re-run planning for remaining items within the same session.
- Extended duplicate handling workflow (flag, suggest consolidate folder, allow mark-as-reference).
- Expanded file-type support (audio metadata, additional office formats, RAW images).

### Should Have
- Quick filters (e.g., "show low-confidence", "show duplicates") in the planning board.
- Session bookmarking so users can pause review and resume later with plan state intact.
- Onboarding wizards to help configure remote vs local models and data access permissions.

### Out of Scope
- Continuous watchers / smart folders (pushed to V3+).
- Cloud integrations (e.g., Google Drive) and semantic search.

## Experience Flow Upgrades
1. User selects target directories (multi-root selection up to 3 folders per run).
2. Configuration step allows picking model provider per task (remote vs local) and setting run-level rules.
3. Scan & planning pipeline surfaces visual cluster map and enriched rationale cards.
4. Users can store decisions as reusable templates (e.g., "Photography workflow") for later quick apply.
5. Session can be saved mid-review; returning resumes the exact approval state.

## Technical Specification
### Architecture Adjustments
- Introduce a persistent preference store (SQLite with SQLCipher) accessible through Agno tool `preference_store`.
- Add model router module handling provider discovery, health checks, and latency monitoring.
- UI updates to render visual cluster snapshots (generated server-side as SVG/PNG) and rename previews.
- Expand backend to support batched execution with dry-run recalculation after partial approvals.

### Module Updates
- **Preference Manager**: CRUD for rules, thresholds, ignored paths; attaches to plan generation to auto-apply defaults.
- **Model Router**: chooses between remote API (OpenAI-compatible) and local Ollama; tracks usage stats.
- **Visualization Service**: uses Constella embeddings to produce static UMAP scatter plot with cluster legends (rendered via matplotlib/plotly in headless mode).
- **Rename Service**: advanced prompt templates referencing content summaries, EXIF data, and user-defined naming schemes.
- **Audit Trail**: append-only ledger capturing plan decisions, overrides, and reasons for rejection.

### Workflow Evolution
```
load_preferences -> scan_roots -> extract -> constella_cluster -> generate_visuals -> generate_plan -> apply_templates -> await_review -> execute_batch -> update_preferences -> persist_audit
```
- After execution, rejected items feed back into preference hints (e.g., suggest new rule).

### Tooling & Integrations
- Agno MCP additions: `preference_store`, `model_router`, `cluster_visualizer`.
- Ollama bridge (HTTP API) pre-configured for local model invocation with fallback to remote provider.
- LiteLLM routing extended to support provider weighting and cost ceilings.

### Data Management
- Preference DB encrypted with user-provided passphrase stored via keychain; fallback to OS-protected storage.
- Visual assets cached per session for reuse when re-opening the plan.

### UI/UX Enhancements
- Tabs for "Folders", "Files", "Duplicates", "Renames" views.
- Hover tooltips referencing cluster exemplar files.
- Progress tracker showing pipeline stage with estimated completion times.
- Pause/Resume button mid-pipeline for long extractions.

### Security & Privacy
- Toggle for "local-only" mode preventing outbound LLM calls; ensures fallback heuristics for summarisation.
- Redact sensitive text snippets in UI (e.g., detect PII/custom regex) unless user clicks "reveal".
- Strengthen path allowlists with templated rules (never touch ~/Library, etc.).

### Observability & Logging
- Aggregated metrics dashboard accessible via UI (num files scanned, time per stage, confidence distribution).
- Exportable audit log (JSON/CSV) containing user decisions for compliance.

### Performance Targets
- Handle up to 15k files with incremental plan generation under 5 minutes on Apple silicon baseline.
- Support resumable scans to avoid re-processing unchanged files when resuming.

## Technical Requirements
### Runtime & Frameworks
- Continue Python 3.11 backend; add `uvloop` for improved async file operations.
- Frontend leverages React Query/RTK Query for state synchronization with backend sessions.

### Libraries & Services
- `sqlalchemy`/`sqlmodel` with `sqlcipher` for encrypted preferences.
- `umap-learn` and `matplotlib` (headless) for visualizations.
- `ollama-python` client for local model interaction.
- `rapidfuzz` for fuzzy matching in rename suggestions and duplicate grouping.

### Configuration
- Settings UI to manage provider credentials, local model downloads, and default run templates.
- Introduce `~/.filevyasa/config.yaml` with encrypted fields for provider keys and preferences.

### Storage & Filesystem
- Cache directory for embeddings, cluster visuals, and rename previews with cleanup policy (LRU).
- Extend rollback store to retain history for 30 days with automatic pruning.

### Testing & Validation
- Add integration tests covering preference persistence, Ollama fallback, and visual asset generation.
- UI snapshot tests for new planning tabs and rename tray.
- Load testing scripts to simulate multi-root scans.

### Deployment & Packaging
- Update Tauri bundle to include assets for visualizations and handle larger binary size.
- Provide environment diagnostics screen to validate Ollama installation before first run.

## Acceptance Criteria
- Users can switch between remote and local models within the same session.
- Preferences applied automatically reduce repeated manual overrides by at least 50% in test scenarios.
- Session pause/resume preserves full plan state and logs without corruption.

## Risks & Mitigations
- **Local Model Drift**: Provide compatibility checks and recommended model list; fallback to remote providers.
- **Visualization Overhead**: Generate thumbnails asynchronously and stream to UI once ready.
- **Preference Conflicts**: Detect contradictory rules and prompt user to resolve before plan generation.

## Follow-up Items
- Explore packaging local models (weights) or providing guided download flows.
- Design interface hooks for upcoming smart folders (V3) to ensure data model alignment.
