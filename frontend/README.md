# FileVyasa Frontend

Tauri desktop application frontend for FileVyasa - an AI-powered local file organizer.

## Tech Stack

- **Framework**: Tauri 2.x + Vite + React 18 (TypeScript)
- **Styling**: Tailwind CSS v4 (dark theme)
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Icons**: Lucide React
- **UI Components**: Radix UI primitives

## Prerequisites

- Node.js 18+
- pnpm
- Rust (for Tauri)
- Backend server running on `http://127.0.0.1:8000`

## Getting Started

1. Install dependencies:
   ```bash
   pnpm install
   ```

2. Start the development server (frontend only):
   ```bash
   pnpm dev
   ```

3. Start Tauri development mode (opens desktop app):
   ```bash
   pnpm tauri:dev
   ```

## Building

Build for production:
```bash
pnpm tauri:build
```

The built application will be available in:
- macOS: `src-tauri/target/release/bundle/macos/FileVyasa.app`
- Windows: `src-tauri/target/release/bundle/msi/` or `src-tauri/target/release/bundle/nsis/`
- Linux: `src-tauri/target/release/bundle/appimage/` or `src-tauri/target/release/bundle/deb/`

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client for backend communication
│   ├── components/       # React components
│   │   ├── common/       # Reusable UI components (Button, Badge, Spinner)
│   │   ├── files/        # File list and detail views
│   │   ├── layout/       # Layout components (Sidebar, Header)
│   │   ├── scan/         # Scan-related components
│   │   └── settings/     # Settings panel
│   ├── lib/              # Utility functions
│   ├── stores/           # Zustand state stores
│   ├── types/            # TypeScript type definitions
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── src-tauri/            # Tauri (Rust) backend
│   ├── src/              # Rust source code
│   ├── Cargo.toml        # Rust dependencies
│   └── tauri.conf.json   # Tauri configuration
└── package.json
```

## Features (v1.1 & v1.2)

- **Folder Scanner**: Select a folder and scan all files
- **File List**: View scanned files with sorting and filtering
- **AI Summaries**: View AI-generated summaries for each file
- **File Details**: Click a file to see detailed metadata, EXIF data, and content preview
- **Category Filters**: Filter by file category (Document, Image, Video, etc.)
- **Search**: Search files by filename
- **Recent Scans**: View and re-open previous scan sessions
- **Settings**: Configure LLM provider, model, and API key

## Development Notes

- The backend must be running for the app to function
- Backend API is expected at `http://127.0.0.1:8000/api`
- The app uses Tauri's dialog plugin for native folder selection
