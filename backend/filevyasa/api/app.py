"""FastAPI application setup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from filevyasa.config import settings
from filevyasa.db.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
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
    from filevyasa.api.routes import scan, files, config
    app.include_router(scan.router, prefix="/api/scan", tags=["scan"])
    app.include_router(files.router, prefix="/api/files", tags=["files"])
    app.include_router(config.router, prefix="/api/config", tags=["config"])
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.1.0"}
    
    return app


# Create default app instance
app = create_app()
