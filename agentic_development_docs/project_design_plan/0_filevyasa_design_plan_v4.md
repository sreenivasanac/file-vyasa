# FileVyasa Design Plan — V4

## Product Vision
Achieve a "never organize again" experience through autonomous but supervised agents that provide semantic discovery, continuous organisation, deep integrations, and enterprise-grade safety nets.

## Strategic Pillars
- **Always-On Intelligence**: background smart folders, scheduled runs, and proactive recommendations.
- **Semantic Understanding**: powerful search, question answering, and policy-driven organisation using vector retrieval and multimodal embeddings.
- **Cross-Platform Reach**: integrate cloud storage, cross-device syncing, and API access for third-party automation.
- **Enterprise Trust**: granular auditing, rollback, policy enforcement, and compliance-ready controls.

## Feature Scope
### Must Deliver
- Smart Folder engine that watches designated directories, auto-creates subfolders, and sorts incoming files based on learned patterns with human-configurable guardrails.
- Semantic search and command interface ("Find client payment terms") powered by vector search + summarisation responses.
- OCR pipeline for non-text PDFs and images (Tesseract/TrOCR) integrated into extraction and search indexes.
- Comprehensive rollback console with point-in-time restore (undo by timestamp, by tag, or by session ID) and CLI bindings (`easy_rollback_system.py`).
- Cloud storage integration starting with Google Drive (scan + plan + execute with same review workflow).
- Multi-agent coordination (planner/executor/watchers) orchestrated via Agno scheduling with retry/backoff.
- Policy manager enabling admin-level rules (protected paths, retention policies, compliance checks) with enforcement before execution.

### Should Deliver
- Batch/parallel processing across CPU cores or distributed nodes for massive directories.
- Cross-device sync of preferences, workflows, and knowledge base via encrypted cloud vault.
- Integration hooks (REST/gRPC) allowing external apps to trigger organisation runs or query semantic search.
- Activity dashboards with trend analytics (files organised per week, confidence stats, automation savings).

### Nice to Have
- Plugin marketplace concept for community-shared workflows and knowledge packs.
- Voice interface layer for issuing commands ("Organise Downloads now").

## Experience Blueprint
1. User promotes frequently used folders to Smart Folders, defining automation scope (auto-apply thresholds, schedule).
2. Watcher agent monitors FS events, triggers planner agent to run dry-run; notifications summarise recommendations.
3. User reviews automation queue via dashboard, optionally enabling auto-verification for recurrent patterns.
4. Semantic command bar allows natural-language queries and operations ("Show all Q2 invoices") with direct action links.
5. Rollback console displays timeline filterable by folder, date, and automation rule; one-click revert or CLI commands apply.
6. Cloud integration surfaces remote Drive folders in same planning UI; operations executed via Drive API with conflict resolution.

## Technical Specification
### Architecture Evolution
- Introduce orchestrator service (e.g., `Temporal`, `Celery` + beat) managing scheduled workflows, watchers, and retries.
- Implement file-system watcher adapters per OS (macOS FSEvents, inotify, Windows USN Journal) abstracted through Agno tools.
- Deploy vector search infrastructure (e.g., `weaviate`, `qdrant`, or managed service) for semantic search across multimodal embeddings.
- Add microservice boundaries: `planner`, `executor`, `search`, `watcher`, `policy` services communicating via message bus (NATS/Kafka-lite).
- Provide public API (REST/gRPC) with auth tokens for external integrations.

### Modules & Services
- **Smart Folder Service**: maintains automation rules, monitors triggers, queues plans, executes auto-approved actions while logging differentials.
- **Semantic Engine**: pipelines embeddings (text, image, audio) using multimodal models, indexes in vector DB, handles search + summarise queries.
- **OCR Service**: scalable workers performing OCR (Tesseract, PaddleOCR) with caching of results and language detection.
- **Rollback Manager**: stores snapshots of actions in append-only ledger with delta indexing + CLI interface.
- **Cloud Connector**: OAuth2 flow for Google Drive, file metadata sync, remote move/rename with conflict mitigation.
- **Policy Engine**: rule evaluation (YAML/DSL) enforcing compliance checks before executor receives actions.
- **Analytics & Reporting**: aggregates data for dashboards, exports metrics to Prometheus-compatible endpoints.

### Workflow Overview
```
watcher_event -> policy_prefilter -> planner_agent -> semantic_context_enrichment -> auto_approval_check -> executor_agent -> rollback_log -> analytics_ingest

search_query -> semantic_engine -> policy_filter -> response_generator (answer + actionable links)
```

### Tooling & Integrations
- Agno MCP expansions: `fs_watcher`, `smart_folder_manager`, `semantic_search`, `ocr_service`, `cloud_connector`, `policy_evaluator`, `rollback_console`.
- Integrate `qdrant`/`weaviate` vector DB with hybrid search (keyword + vector) for robust retrieval.
- Use `Temporal` or `Celery` for scheduling + retries; `redis`/`rabbitmq` as broker.
- Add `google-api-python-client` for Drive operations with exponential backoff.

### Data Strategy
- Multi-tenant metadata store (PostgreSQL) holding automation rules, activity logs, semantic indexes references.
- Versioned rollback snapshots with deduplicated file hashes stored in compressed form when feasible.
- Encrypted sync vault hosted by user-selected storage (e.g., iCloud Drive, Dropbox) for cross-device configs.

### UI/UX Requirements
- Automation dashboard summarising smart folder statuses, upcoming runs, alerts for manual review.
- Command palette with natural-language queries returning cards (results, recommended actions, quick filters).
- Rollback console with timeline slider, search, and CLI command references.
- Integration settings page for connecting cloud accounts, managing API tokens, and reviewing access logs.

### Security & Compliance
- Role-based access control for multi-user/team mode with scoped permissions.
- Detailed audit trails compliant with SOC2-style logging (who approved, when, action metadata).
- Encryption in transit (mTLS between services) and at rest (PostgreSQL TDE, vector DB encryption where available).
- Privacy controls for cloud operations (scope-limited OAuth, activity alerts when remote files accessed).

### Observability & SRE
- Centralised logging with structured context (ELK/Opensearch stack).
- Metrics via Prometheus + Grafana dashboards for workflow latency, success rates, queue depth.
- Alerting rules for failed automation runs, watcher disconnects, or search index lag.

### Performance Targets
- Smart folders should react within <30 seconds of file arrival (for directories <1k new files per hour).
- Semantic search results returned under 2 seconds for corpus up to 1M documents with hardware acceleration.
- Rollback operations complete within 10 seconds for batches up to 10k actions using incremental snapshots.

## Technical Requirements
### Runtime & Deployment
- Modular services deployable as Docker containers; support for Kubernetes or self-hosted orchestrator.
- Provide desktop bundle that ships lightweight orchestrator or connects to remote headless backend.
- Include CLI tools for advanced automation and integration with `crontab`/CI pipelines.

### Libraries & Services
- `watchdog` plus OS-specific watchers for filesystem events.
- `temporalio` or `celery` for orchestration.
- `google-api-python-client`, `google-auth` for Drive integration.
- `ocrmypdf`, `pytesseract`, `torch` + `microsoft/trocr` models for OCR.
- `sentence-transformers` multimodal variants, `clip`/`laion` embeddings for images.
- `qdrant-client`/`weaviate-client` for vector DB integration.
- `fastapi`/`grpclib` for API surfaces.

### Configuration & Policies
- Central `policy.yaml` supporting declarative rules (e.g., `retain: Finance/* for 7 years`).
- Automation schedules defined via cron-like syntax stored in orchestrator.
- API token management interface with rotation reminders and activity logs.

### Storage & Filesystem
- Dedicate storage layer for snapshots/rollback (e.g., local ZFS dataset or object storage) with retention policies.
- Ensure cross-platform path normalization and symlink safety for smart folders.

### Testing & Validation
- Simulation harness generating synthetic file events to validate smart folder logic.
- Chaos testing for orchestrator (simulate worker failure, network instability).
- Security tests (penetration, policy bypass attempts) and compliance audits.
- Benchmark suites for semantic search latency and OCR throughput.

### Deployment & Distribution
- Option to run backend headless on home server/NAS with desktop client acting as thin UI.
- Provide update channels (stable/beta) with feature flags toggling advanced automation.
- Cloud integration packaging includes consent screens and data usage breakdown.

## Acceptance Criteria
- Smart folders autonomously maintain organisation with override controls and clear audit logs.
- Semantic search returns relevant results and links directly to organise/preview actions.
- Rollback console allows undo by time range, batch ID, or automation rule within defined SLAs.
- Cloud integration executes safe rename/move operations with same transparency as local operations.

## Risks & Mitigations
- **Automation Missteps**: Strict policy gates, auto-apply caps, continuous learning from rollback feedback.
- **Privacy Concerns**: Provide detailed telemetry opt-outs, on-device processing options, granular consent for cloud sync.
- **Operational Complexity**: Offer guided setup, pre-flight diagnostics, and managed presets for advanced features.
- **Scalability**: Adopt modular microservices with autoscaling, caching, and efficient index maintenance.

## Future Horizons
- Extend integrations to additional cloud providers (OneDrive, Dropbox) and enterprise storage (SharePoint/NAS).
- Introduce federated learning of organisation patterns while preserving privacy via local differential updates.
- Offer developer SDK for custom agents/tools plugging into FileVyasa ecosystem.
