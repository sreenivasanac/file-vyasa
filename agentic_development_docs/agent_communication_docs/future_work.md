# FileVyasa Future Work

## v1.3 (Next)

### Clustering Module (Constella Integration)
- [ ] Integrate Constella library from `/Users/sreenivasanac/SoftwareProjects/constella`
- [ ] Convert FileObjects to Constella ContentUnits
- [ ] Generate embeddings via LiteLLM
- [ ] Run K-Means clustering for file grouping
- [ ] Create folder planning board UI endpoint

### Folder Planning Preview
- [ ] Generate proposed folder structure from clusters
- [ ] API endpoint for plan preview
- [ ] Cluster-to-folder name mapping via LLM

## v1.4 (Planned)

### File Operation Planning
- [ ] Per-file action computation (move/rename)
- [ ] Folder organization scoring
- [ ] Approval state manager

### Confidence System
- [ ] Confidence calculation for proposed actions
- [ ] Green/yellow/red threshold indicators

## v1.5 (Planned)

### Safe Execution
- [ ] Execute approved move/rename actions
- [ ] Rollback metadata recording
- [ ] "No delete" safety guardrails

### Duplicate Detection
- [ ] SHA-256 file hashing
- [ ] Duplicate detection and flagging
- [ ] Content hash storage in FileObjectTable (already has field)

## TODOs in Code

Search for `TODO` comments in the codebase for minor improvements:
- Content extraction improvements for specific formats
- Better error handling for edge cases
- Performance optimizations for large directories

## Frontend TODOs (v1.1/v1.2 implemented)

### Completed
- [x] Tauri project setup with Vite + React + TypeScript
- [x] Dark theme with Tailwind CSS
- [x] Sidebar navigation (Scan, Files, Recent, Settings)
- [x] Folder picker using Tauri dialog plugin
- [x] Scan progress indicator with polling
- [x] File list table with pagination
- [x] Category filters and search
- [x] File detail panel (metadata, AI summaries, EXIF)
- [x] Settings page for LLM configuration
- [x] Recent scans view

### Frontend Enhancements (Future)
- [ ] Light theme toggle
- [ ] Configurable backend URL (currently hardcoded)
- [ ] File preview thumbnails for images
- [ ] Sortable table columns
- [ ] Keyboard navigation
- [ ] Drag-and-drop folder selection
- [ ] "Open in Finder/Explorer" button for files
- [ ] Export file list to CSV
- [ ] Bulk file selection
- [ ] Category statistics visualization (charts)

### v1.3 Frontend (Planned)
- [ ] Folder planning board UI
- [ ] Cluster visualization
- [ ] Drag-and-drop file reassignment between clusters
- [ ] Proposed folder name editing

### v1.4/v1.5 Frontend (Planned)
- [ ] Action approval queue UI
- [ ] Confidence color indicators (green/yellow/red)
- [ ] Execution progress UI
- [ ] Session summary view
- [ ] Rollback UI

## Known Limitations

1. **Video/Audio**: Currently only extracts metadata, no content analysis
2. **Archives**: Only metadata, no content inspection
3. **OCR**: Not implemented (planned for v4)
4. **Local LLM**: Ollama support deferred to v2
5. **Multi-root**: Single directory scan only (multi-root in v2)
6. **Backend URL**: Hardcoded to localhost:8000 in frontend
