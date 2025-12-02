"""FastAPI application setup."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from filevyasa.config import settings
from filevyasa.db.connection import init_db


def _configure_logging():
    """Configure logging to suppress noisy third-party warnings.
    
    pdfminer warnings cannot be fixed at the code level - they indicate:
    - FontBBox: Malformed PDFs with incomplete font descriptors (common in Office exports)
    - Paint color: Non-standard color space definitions in PDFs
    These are issues with source PDFs, not bugs. Text extraction still works correctly.
    """
    # Suppress pdfminer font/interp warnings (caused by malformed PDFs, not fixable)
    logging.getLogger("pdfminer.pdffont").setLevel(logging.ERROR)
    logging.getLogger("pdfminer.pdfinterp").setLevel(logging.ERROR)
    logging.getLogger("pdfminer.pdfpage").setLevel(logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    _configure_logging()
    init_db()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="AI-Powered Local File Organizer API",
        version="1.1.0",
        lifespan=lifespan,
    )

    # Configure CORS for Tauri/local frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all for local development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from filevyasa.api.routes import config, files, folders
    app.include_router(folders.router, prefix="/api/folders", tags=["folders"])
    app.include_router(files.router, prefix="/api/files", tags=["files"])
    app.include_router(config.router, prefix="/api/config", tags=["config"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.1.0"}

    return app


# Create default app instance
app = create_app()
