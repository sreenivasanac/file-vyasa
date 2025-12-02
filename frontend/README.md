# FileVyasa Frontend

Cross-platform desktop app built with Tauri + React.

## Tech Stack

- **Framework**: Tauri 2.x + Vite + React 19 (TypeScript)
- **Styling**: Tailwind CSS v4 (dark theme)
- **State**: Zustand + TanStack Query
- **UI**: Radix UI primitives + Lucide icons

## Quick Start

```bash
pnpm install
pnpm tauri:dev
```

Requires the backend running at `http://127.0.0.1:8000`.

## Building

```bash
pnpm tauri:build
```

Outputs:
- macOS: `src-tauri/target/release/bundle/macos/FileVyasa.app`
- Windows: `src-tauri/target/release/bundle/msi/`
- Linux: `src-tauri/target/release/bundle/appimage/`

## Project Structure

```
frontend/
├── src/
│   ├── api/           # Backend API client
│   ├── components/
│   │   ├── common/    # Button, Badge, Spinner
│   │   ├── files/     # File list, detail views
│   │   ├── folders/   # Folder management
│   │   ├── layout/    # Sidebar, Header
│   │   └── settings/  # Settings panel
│   ├── stores/        # Zustand stores
│   └── types/         # TypeScript definitions
└── src-tauri/         # Tauri Rust backend
```

## Features

- **Folder Management** — Add/remove folders to monitor
- **File Browser** — List view with sorting, filtering, search
- **File Details** — Metadata, EXIF data, content preview, AI summary
- **Category Filters** — Filter by Document, Image, Media, Code, etc.
- **Settings** — Configure LLM provider and model

## Development

```bash
pnpm dev        # Web-only dev server
pnpm tauri:dev  # Full desktop app
pnpm lint       # ESLint
pnpm build      # Production build
```
