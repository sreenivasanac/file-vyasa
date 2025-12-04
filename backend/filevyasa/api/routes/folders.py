"""Folder API endpoints for managing monitored folders and sync operations."""

import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException

from filevyasa.config import settings
from filevyasa.db.connection import get_session
from filevyasa.db.tables import MonitoredFolderTable
from filevyasa.models.enums import FolderStatus
from filevyasa.models.folder import (
    FolderSyncRequest,
    MonitoredFolderCreate,
    MonitoredFolderResponse,
)
from filevyasa.sync import CancellationManager, ProcessingTracker, SyncService

logger = structlog.get_logger()

router = APIRouter()


# --- Helper Functions ---

@contextmanager
def db_session():
    """Context manager for database sessions."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()

def _check_folder_conflicts(
    root_path: str, exclude_folder_id: Optional[str] = None
) -> Optional[str]:
    """Check if the given path conflicts with existing monitored folders.

    Returns the conflicting folder's root_path if there's a conflict, None otherwise.
    A conflict occurs if one path is a subfolder of another.
    """
    with db_session() as session:
        folders = session.query(MonitoredFolderTable).all()
        new_path = Path(root_path).resolve()

        for folder in folders:
            if exclude_folder_id and folder.id == exclude_folder_id:
                continue

            existing_path = Path(folder.root_path).resolve()

            # Check if one is subfolder of the other
            try:
                new_path.relative_to(existing_path)
                return folder.root_path
            except ValueError:
                pass

            try:
                existing_path.relative_to(new_path)
                return folder.root_path
            except ValueError:
                pass

        return None


def _folder_to_response(folder: MonitoredFolderTable) -> MonitoredFolderResponse:
    """Convert MonitoredFolderTable to MonitoredFolderResponse."""
    return MonitoredFolderResponse(
        id=folder.id,
        root_path=folder.root_path,
        name=folder.name,
        status=FolderStatus(folder.status),
        last_synced_at=folder.last_synced_at,
        last_llm_model=folder.last_llm_model,
        total_files=folder.total_files,
        processed_files=folder.processed_files,
        failed_files=folder.failed_files,
        generate_document_summaries=folder.generate_document_summaries,
        generate_image_descriptions=folder.generate_image_descriptions,
        extract_media_transcriptions=folder.extract_media_transcriptions,
        ignore_patterns=folder.ignore_patterns or [],
        created_at=folder.created_at,
    )


async def _check_llava_available() -> dict:
    """Check if Ollama llava model is available."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                return {
                    "available": False,
                    "reason": "Ollama is not running. Start it with: ollama serve"
                }

            models = response.json().get("models", [])
            llava_available = any(
                m.get("name", "").startswith("llava") for m in models
            )

            if llava_available:
                return {"available": True, "reason": None}
            else:
                return {
                    "available": False,
                    "reason": "llava model not installed. Run: ollama pull llava"
                }

    except httpx.ConnectError:
        return {
            "available": False,
            "reason": "Cannot connect to Ollama. Start it with: ollama serve"
        }
    except Exception as e:
        return {"available": False, "reason": f"Error checking Ollama: {e}"}


def _run_sync_task(
    folder_id: str,
    generate_document_summaries: bool,
    generate_image_descriptions: bool,
    extract_media_transcriptions: bool,
):
    """Background task wrapper for SyncService."""
    service = SyncService(
        folder_id=folder_id,
        generate_document_summaries=generate_document_summaries,
        generate_image_descriptions=generate_image_descriptions,
        extract_media_transcriptions=extract_media_transcriptions,
    )
    service.run()


# --- API Endpoints ---

@router.post("", response_model=MonitoredFolderResponse)
async def add_folder(
    request: MonitoredFolderCreate, background_tasks: BackgroundTasks
):
    """Add a new folder to monitor. Auto-syncs after adding.

    Validates:
    - Path exists and is a directory
    - Path is not already monitored
    - Path does not conflict with existing folders (no nesting)
    - If image descriptions enabled, Ollama llava model must be available
    """
    # Validate path exists
    if not os.path.exists(request.root_path):
        raise HTTPException(status_code=400, detail=f"Path does not exist: {request.root_path}")
    if not os.path.isdir(request.root_path):
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.root_path}")

    # Check llava availability if image descriptions enabled
    if request.generate_image_descriptions:
        llava_status = await _check_llava_available()
        if not llava_status["available"]:
            raise HTTPException(
                status_code=400,
                detail=f"Image descriptions require Ollama llava model. {llava_status['reason']}"
            )

    # Check for conflicts with existing folders
    conflict = _check_folder_conflicts(request.root_path)
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This folder conflicts with an existing monitored folder: "
                f"{conflict}. Please remove one of the folders first."
            ),
        )

    with db_session() as session:
        # Check if already exists
        existing = session.query(MonitoredFolderTable).filter_by(
            root_path=request.root_path
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Folder is already being monitored: {request.root_path}",
            )

        # Combine ignore patterns
        ignore_patterns = list(settings.default_ignore_patterns)
        if request.ignore_patterns:
            ignore_patterns.extend(request.ignore_patterns)

        # Create folder record
        folder_id = str(uuid4())
        folder_name = Path(request.root_path).name or request.root_path

        folder = MonitoredFolderTable(
            id=folder_id,
            root_path=request.root_path,
            name=folder_name,
            status=FolderStatus.IDLE.value,
            generate_document_summaries=request.generate_document_summaries,
            generate_image_descriptions=request.generate_image_descriptions,
            extract_media_transcriptions=request.extract_media_transcriptions,
            ignore_patterns=ignore_patterns,
            created_at=datetime.now(),
        )
        session.add(folder)
        session.commit()

        result = _folder_to_response(folder)

    # Auto-sync in background
    background_tasks.add_task(
        _run_sync_task,
        folder_id,
        request.generate_document_summaries,
        request.generate_image_descriptions,
        request.extract_media_transcriptions,
    )

    return result


@router.get("", response_model=List[MonitoredFolderResponse])
async def list_folders():
    """List all monitored folders."""
    with db_session() as session:
        folders = session.query(MonitoredFolderTable).order_by(
            MonitoredFolderTable.created_at.desc()
        ).all()
        return [_folder_to_response(f) for f in folders]


@router.get("/{folder_id}", response_model=MonitoredFolderResponse)
async def get_folder(folder_id: str):
    """Get details of a specific monitored folder."""
    with db_session() as session:
        folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
        if not folder:
            raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")
        return _folder_to_response(folder)


@router.delete("/{folder_id}")
async def delete_folder(folder_id: str):
    """Remove a folder from monitoring.

    This only removes the folder from the app's database.
    The actual files on disk are NOT deleted.
    """
    with db_session() as session:
        folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
        if not folder:
            raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

        session.delete(folder)
        session.commit()

    return {"message": "Folder removed from monitoring", "folder_id": folder_id}


@router.post("/{folder_id}/sync", response_model=MonitoredFolderResponse)
async def sync_folder(
    folder_id: str,
    request: Optional[FolderSyncRequest] = None,
    background_tasks: BackgroundTasks = None
):
    """Sync a folder - detect and process new/modified/deleted files."""
    with db_session() as session:
        folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
        if not folder:
            raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

        if folder.status == FolderStatus.SYNCING.value:
            raise HTTPException(status_code=409, detail="Folder is already syncing")

        # Determine AI processing settings (use request overrides if provided)
        generate_document_summaries = folder.generate_document_summaries
        generate_image_descriptions = folder.generate_image_descriptions
        extract_media_transcriptions = folder.extract_media_transcriptions

        if request:
            if request.generate_document_summaries is not None:
                generate_document_summaries = request.generate_document_summaries
            if request.generate_image_descriptions is not None:
                generate_image_descriptions = request.generate_image_descriptions
            if request.extract_media_transcriptions is not None:
                extract_media_transcriptions = request.extract_media_transcriptions

        # Reset progress counters
        folder.processed_files = 0
        folder.failed_files = 0
        folder.status = FolderStatus.SYNCING.value
        session.commit()

        result = _folder_to_response(folder)

    # Start sync in background
    background_tasks.add_task(
        _run_sync_task,
        folder_id,
        generate_document_summaries,
        generate_image_descriptions,
        extract_media_transcriptions,
    )

    return result


@router.post("/{folder_id}/cancel")
async def cancel_sync(folder_id: str):
    """Cancel an ongoing sync operation.

    Sets both the in-memory cancellation flag (for immediate response)
    and the database status (for persistence).
    """
    # Signal cancellation immediately via in-memory flag
    CancellationManager.cancel(folder_id)

    with db_session() as session:
        folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
        if not folder:
            raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

        if folder.status == FolderStatus.SYNCING.value:
            folder.status = FolderStatus.CANCELLED.value
            session.commit()
    return {"folder_id": folder_id, "status": "cancelled"}


@router.get("/{folder_id}/processing")
async def get_processing_files(folder_id: str):
    """Get the list of files currently being processed for a folder.

    Returns a list of files that are actively being processed during sync.
    This enables real-time UI updates showing which files are being worked on.
    """
    with db_session() as session:
        folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()

    if not folder:
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

    processing_files = ProcessingTracker.get_processing_files(folder_id)
    return {"folder_id": folder_id, "processing_files": processing_files}
