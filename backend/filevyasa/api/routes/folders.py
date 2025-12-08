"""Folder API endpoints for managing monitored folders and sync operations."""

import os
from typing import List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException

from filevyasa.db.folder_repository import (
    FolderAlreadyMonitoredError,
    FolderNotFoundError,
    FolderSyncAlreadyRunningError,
    create_monitored_folder,
)
from filevyasa.db.folder_repository import (
    cancel_folder_sync as db_cancel_folder_sync,
)
from filevyasa.db.folder_repository import (
    check_folder_conflicts as db_check_folder_conflicts,
)
from filevyasa.db.folder_repository import (
    delete_folder as db_delete_folder,
)
from filevyasa.db.folder_repository import (
    folder_exists as db_folder_exists,
)
from filevyasa.db.folder_repository import (
    get_folder as db_get_folder,
)
from filevyasa.db.folder_repository import (
    list_folders as db_list_folders,
)
from filevyasa.db.folder_repository import (
    prepare_folder_sync as db_prepare_folder_sync,
)
from filevyasa.llm import check_llava_available
from filevyasa.models.folder import (
    FolderSyncRequest,
    MonitoredFolderCreate,
    MonitoredFolderResponse,
)
from filevyasa.sync import CancellationManager, ProcessingTracker, SyncService

logger = structlog.get_logger()

router = APIRouter()


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
        llava_status = await check_llava_available()
        if not llava_status["available"]:
            raise HTTPException(
                status_code=400,
                detail=f"Image descriptions require Ollama llava model. {llava_status['reason']}",
            )

    # Check for conflicts with existing folders
    conflict = db_check_folder_conflicts(request.root_path)
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=(
                "This folder conflicts with an existing monitored folder: "
                f"{conflict}. Please remove one of the folders first."
            ),
        )

    try:
        folder = create_monitored_folder(
            root_path=request.root_path,
            generate_document_summaries=request.generate_document_summaries,
            generate_image_descriptions=request.generate_image_descriptions,
            extract_media_transcriptions=request.extract_media_transcriptions,
            ignore_patterns=request.ignore_patterns,
            excluded_paths=request.excluded_paths,
        )
    except FolderAlreadyMonitoredError:
        raise HTTPException(
            status_code=409,
            detail=f"Folder is already being monitored: {request.root_path}",
        ) from None

    # Auto-sync in background
    background_tasks.add_task(
        _run_sync_task,
        folder.id,
        folder.generate_document_summaries,
        folder.generate_image_descriptions,
        folder.extract_media_transcriptions,
    )

    return folder


@router.get("", response_model=List[MonitoredFolderResponse])
async def list_folders():
    """List all monitored folders."""
    return db_list_folders()


@router.get("/{folder_id}", response_model=MonitoredFolderResponse)
async def get_folder(folder_id: str):
    """Get details of a specific monitored folder."""
    folder = db_get_folder(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")
    return folder


@router.delete("/{folder_id}")
async def delete_folder(folder_id: str):
    """Remove a folder from monitoring.

    This only removes the folder from the app's database.
    The actual files on disk are NOT deleted.
    """
    if not db_delete_folder(folder_id):
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

    return {"message": "Folder removed from monitoring", "folder_id": folder_id}


@router.post("/{folder_id}/sync", response_model=MonitoredFolderResponse)
async def sync_folder(
    folder_id: str,
    request: Optional[FolderSyncRequest] = None,
    background_tasks: BackgroundTasks = None,
):
    """Sync a folder - detect and process new/modified/deleted files."""
    try:
        (
            folder,
            generate_document_summaries,
            generate_image_descriptions,
            extract_media_transcriptions,
        ) = db_prepare_folder_sync(folder_id, request)
    except FolderNotFoundError:
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}") from None
    except FolderSyncAlreadyRunningError:
        raise HTTPException(status_code=409, detail="Folder is already syncing") from None

    # Start sync in background
    background_tasks.add_task(
        _run_sync_task,
        folder_id,
        generate_document_summaries,
        generate_image_descriptions,
        extract_media_transcriptions,
    )

    return folder


@router.post("/{folder_id}/cancel")
async def cancel_sync(folder_id: str):
    """Cancel an ongoing sync operation.

    Sets both the in-memory cancellation flag (for immediate response)
    and the database status (for persistence).
    """
    # Signal cancellation immediately via in-memory flag
    CancellationManager.cancel(folder_id)

    if not db_cancel_folder_sync(folder_id):
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")
    return {"folder_id": folder_id, "status": "cancelled"}


@router.get("/{folder_id}/sync-status")
async def get_sync_status(folder_id: str):
    """Get folder sync status and currently processing files in one call.

    Returns folder details along with the list of files being processed.
    This enables efficient polling during sync with a single API call.
    """
    folder = db_get_folder(folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

    processing_files = ProcessingTracker.get_processing_files(folder_id)
    return {
        "folder": folder,
        "processing_files": processing_files,
    }


@router.get("/{folder_id}/processing")
async def get_processing_files(folder_id: str):
    """Get the list of files currently being processed for a folder.

    Returns a list of files that are actively being processed during sync.
    This enables real-time UI updates showing which files are being worked on.

    Note: Consider using /sync-status for combined folder + processing data.
    """
    if not db_folder_exists(folder_id):
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

    processing_files = ProcessingTracker.get_processing_files(folder_id)
    return {"folder_id": folder_id, "processing_files": processing_files}
