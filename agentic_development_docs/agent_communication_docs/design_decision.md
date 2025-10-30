# Design Decisions — 2025-10-30

- Adopt SQLite/SQLModel (SQLCipher when available) as the unified local store for session logs, preferences, and rollback metadata across V1–V2 to reduce operational overhead before introducing PostgreSQL in V4.
- Route LLM traffic through LiteLLM so the agent can switch between remote providers and Ollama without custom adapters per version.
- Generate all visual previews server-side and stream to the Tauri UI to keep the frontend lightweight and avoid bundling heavy media libraries in the desktop client.
- Stage automation capabilities incrementally: V1 manual approval only, V2 introduces partial auto-apply within sessions, V3 adds batch auto-apply with evidence, and V4 activates Smart Folders and watchers.
