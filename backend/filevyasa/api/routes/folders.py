"""Folder API endpoints for managing monitored folders and sync operations."""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException

from filevyasa.config import settings
from filevyasa.db.connection import get_session
from filevyasa.db.tables import FileObjectTable, MonitoredFolderTable
from filevyasa.extractor import enrich_file_object
from filevyasa.llm import ImageDescriber, Summarizer, Transcriber
from filevyasa.models.enums import FileCategory, FolderStatus
from filevyasa.models.file_object import FileObject
from filevyasa.models.folder import (
    FolderSyncRequest,
    MonitoredFolderCreate,
    MonitoredFolderResponse,
)
from filevyasa.scanner import Scanner

logger = structlog.get_logger()

router = APIRouter()


# --- Helper Functions ---

def _get_current_llm_model() -> str:
    """Get the currently configured LLM model string."""
    return f"{settings.llm_provider}/{settings.llm_model}"


def _check_folder_conflicts(
    root_path: str, exclude_folder_id: Optional[str] = None
) -> Optional[str]:
    """Check if the given path conflicts with existing monitored folders.

    Returns the conflicting folder's root_path if there's a conflict, None otherwise.
    A conflict occurs if one path is a subfolder of another.
    """
    session = get_session()
    try:
        folders = session.query(MonitoredFolderTable).all()
        new_path = Path(root_path).resolve()

        for folder in folders:
            if exclude_folder_id and folder.id == exclude_folder_id:
                continue

            existing_path = Path(folder.root_path).resolve()

            # Check if one is subfolder of the other
            try:
                new_path.relative_to(existing_path)
                # new_path is inside existing_path
                return folder.root_path
            except ValueError:
                pass

            try:
                existing_path.relative_to(new_path)
                # existing_path is inside new_path
                return folder.root_path
            except ValueError:
                pass

        return None
    finally:
        session.close()


def _get_extraction_status(file_obj: FileObject) -> str:
    """Get extraction status as string value."""
    status = getattr(file_obj, 'extraction_status', 'pending')
    if hasattr(status, 'value'):
        return status.value
    return str(status)


def _format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    size = size_bytes
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _run_sync(
    folder_id: str,
    generate_document_summaries: bool,
    generate_image_descriptions: bool,
    extract_media_transcriptions: bool,
):
    """Background task to sync a folder.

    Sync logic:
    - New files: full extract + AI processing based on file type and settings
    - Modified files (modified_at changed): re-extract + re-process
    - Model changed: re-process only (if AI processing enabled)
    - Unchanged: skip
    - Deleted from disk: remove from DB

    AI Processing by file type:
    - Documents: Generate AI summary (if generate_document_summaries=True)
    - Images: Generate AI description using vision model (if generate_image_descriptions=True)
    - Audio/Video: Transcribe first 10 min and optionally summarize
      (if extract_media_transcriptions=True)
    """
    session = get_session()

    try:
        folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
        if not folder:
            return

        # Update status to syncing
        folder.status = FolderStatus.SYNCING.value
        session.commit()

        current_model = _get_current_llm_model()

        # Initialize AI processors based on settings
        summarizer = Summarizer() if generate_document_summaries else None
        image_describer = None
        transcriber = None

        if generate_image_descriptions:
            # ImageDescriber uses Ollama llava model exclusively
            image_describer = ImageDescriber()

        if extract_media_transcriptions:
            transcriber = Transcriber()

        # Get existing files from DB indexed by path
        existing_files = {
            f.path: f for f in session.query(FileObjectTable).filter_by(folder_id=folder_id).all()
        }

        # Scan filesystem
        ignore_patterns = (
            list(folder.ignore_patterns or [])
            + list(settings.default_ignore_patterns)
        )
        scanner = Scanner(
            ignore_patterns=ignore_patterns,
            folder_id=folder_id
        )
        fs_files = scanner.scan_to_list(folder.root_path, recursive=True)
        fs_paths = {f.path for f in fs_files}

        folder.total_files = len(fs_files)
        session.commit()

        processed = 0
        failed = 0
        new_count = 0
        modified_count = 0
        unchanged_count = 0

        for file_obj in fs_files:
            # Check for cancellation
            session.refresh(folder)
            if folder.status == FolderStatus.CANCELLED.value:
                break

            db_file = existing_files.get(file_obj.path)

            try:
                if db_file is None:
                    # NEW FILE - full processing
                    new_count += 1
                    file_obj = enrich_file_object(file_obj)

                    # Process based on file category
                    file_obj = _process_file_by_category(
                        file_obj,
                        summarizer=summarizer,
                        image_describer=image_describer,
                        transcriber=transcriber,
                        generate_document_summaries=generate_document_summaries
                    )

                    # Insert new file
                    new_db_file = FileObjectTable(
                        id=file_obj.id,
                        folder_id=folder_id,
                        path=file_obj.path,
                        filename=file_obj.filename,
                        extension=file_obj.extension,
                        mime_type=file_obj.mime_type,
                        size_bytes=file_obj.size_bytes,
                        created_at=file_obj.created_at,
                        modified_at=file_obj.modified_at,
                        accessed_at=getattr(file_obj, 'accessed_at', None),
                        is_symlink=getattr(file_obj, 'is_symlink', False),
                        category=(
                            file_obj.category.value
                            if hasattr(file_obj.category, 'value')
                            else str(file_obj.category)
                        ),
                        content_preview=file_obj.content_preview,
                        transcription=getattr(file_obj, 'transcription', None),
                        transcription_duration=getattr(file_obj, 'transcription_duration', None),
                        exif_data=file_obj.exif_data,
                        file_metadata=file_obj.metadata,
                        ai_brief_summary=file_obj.ai_brief_summary,
                        ai_summary=file_obj.ai_summary,
                        llm_model=getattr(file_obj, 'llm_model', None),
                        extraction_status=_get_extraction_status(file_obj),
                        extraction_error=getattr(file_obj, 'extraction_error', None),
                        is_password_protected=getattr(file_obj, 'is_password_protected', False),
                        scanned_at=file_obj.scanned_at,
                        summarized_at=file_obj.summarized_at,
                    )
                    session.add(new_db_file)

                elif (
                    file_obj.modified_at
                    and db_file.modified_at
                    and file_obj.modified_at > db_file.modified_at
                ):
                    # MODIFIED - re-extract + re-process
                    modified_count += 1
                    file_obj = enrich_file_object(file_obj)

                    file_obj = _process_file_by_category(
                        file_obj,
                        summarizer=summarizer,
                        image_describer=image_describer,
                        transcriber=transcriber,
                        generate_document_summaries=generate_document_summaries
                    )

                    # Update existing file
                    db_file.size_bytes = file_obj.size_bytes
                    db_file.modified_at = file_obj.modified_at
                    db_file.accessed_at = getattr(file_obj, 'accessed_at', None)
                    db_file.content_preview = file_obj.content_preview
                    db_file.transcription = getattr(file_obj, 'transcription', None)
                    db_file.transcription_duration = getattr(
                        file_obj, 'transcription_duration', None
                    )
                    db_file.exif_data = file_obj.exif_data
                    db_file.file_metadata = file_obj.metadata
                    db_file.ai_brief_summary = file_obj.ai_brief_summary
                    db_file.ai_summary = file_obj.ai_summary
                    db_file.llm_model = getattr(file_obj, 'llm_model', None)
                    db_file.extraction_status = _get_extraction_status(file_obj)
                    db_file.extraction_error = getattr(file_obj, 'extraction_error', None)
                    db_file.scanned_at = datetime.now()
                    db_file.summarized_at = file_obj.summarized_at

                else:
                    # UNCHANGED - skip
                    unchanged_count += 1
                    continue  # Don't count as processed

                session.commit()
                processed += 1

            except Exception as e:
                logger.error("file_processing_failed", filename=file_obj.filename, error=str(e))
                failed += 1

            # Update progress
            folder.processed_files = processed
            folder.failed_files = failed
            session.commit()

        # Delete files that no longer exist on disk
        deleted_count = 0
        for db_path, db_file in existing_files.items():
            if db_path not in fs_paths:
                session.delete(db_file)
                deleted_count += 1

        # Final update
        session.refresh(folder)
        if folder.status != FolderStatus.CANCELLED.value:
            folder.status = FolderStatus.IDLE.value
            folder.last_synced_at = datetime.now()
            # Store model if any AI processing was enabled
            if generate_document_summaries or generate_image_descriptions:
                folder.last_llm_model = current_model

        folder.total_files = len(fs_paths) - deleted_count
        folder.processed_files = processed
        folder.failed_files = failed
        session.commit()

    except Exception as e:
        import traceback
        print(f"Sync error for folder {folder_id}: {e}")
        traceback.print_exc()
        folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
        if folder:
            folder.status = FolderStatus.ERROR.value
            session.commit()
    finally:
        session.close()


def _process_file_by_category(
    file_obj: FileObject,
    summarizer: Optional[Summarizer],
    image_describer: Optional[ImageDescriber],
    transcriber: Optional[Transcriber],
    generate_document_summaries: bool,
) -> FileObject:
    """Process file based on its category using appropriate AI processor.

    Args:
        file_obj: FileObject to process
        summarizer: Summarizer for document AI summaries
        image_describer: ImageDescriber for vision-based image descriptions
        transcriber: Transcriber for audio/video transcription
        generate_document_summaries: Whether to also summarize transcriptions

    Returns:
        Processed FileObject
    """
    is_non_content_file = (
        file_obj.content_preview and
        file_obj.metadata.get("extraction_method") == "skipped"
    )

    category = file_obj.category
    if hasattr(category, 'value'):
        category_value = category.value
    else:
        category_value = str(category)

    # Image files - use vision model for description
    if category_value == FileCategory.IMAGE.value:
        if image_describer:
            file_obj = image_describer.describe(file_obj)
        elif is_non_content_file:
            file_obj.ai_brief_summary = file_obj.content_preview
            file_obj.ai_summary = file_obj.content_preview
            file_obj.summarized_at = datetime.now()

    # Audio/Video files - transcribe and optionally summarize
    elif category_value in [FileCategory.AUDIO.value, FileCategory.VIDEO.value]:
        if transcriber:
            file_obj = transcriber.transcribe(file_obj)
            # Also generate AI summary of transcription if enabled
            if summarizer and file_obj.transcription and generate_document_summaries:
                # Use transcription as content for summarization
                original_preview = file_obj.content_preview
                file_obj.content_preview = file_obj.transcription[:2000]  # First 2000 chars
                file_obj = summarizer.summarize(file_obj)
                # Keep original metadata preview
                if original_preview and not original_preview.startswith("["):
                    file_obj.content_preview = original_preview + "\n\n[Transcription available]"
        elif is_non_content_file:
            file_obj.ai_brief_summary = file_obj.content_preview
            file_obj.ai_summary = file_obj.content_preview
            file_obj.summarized_at = datetime.now()

    # Document/Text files - use standard summarizer
    elif category_value in [FileCategory.DOCUMENT.value, FileCategory.TEXT.value,
                            FileCategory.SPREADSHEET.value, FileCategory.PRESENTATION.value]:
        if is_non_content_file:
            file_obj.ai_brief_summary = file_obj.content_preview
            file_obj.ai_summary = file_obj.content_preview
            file_obj.llm_model = None
            file_obj.summarized_at = datetime.now()
        elif summarizer and file_obj.content_preview:
            file_obj = summarizer.summarize(file_obj)

    # Other file types - use content if available
    else:
        if is_non_content_file:
            file_obj.ai_brief_summary = file_obj.content_preview
            file_obj.ai_summary = file_obj.content_preview
            file_obj.llm_model = None
            file_obj.summarized_at = datetime.now()
        elif summarizer and file_obj.content_preview:
            file_obj = summarizer.summarize(file_obj)

    return file_obj


# --- API Endpoints ---

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
            )
        )

    session = get_session()

    # Check if already exists
    existing = session.query(MonitoredFolderTable).filter_by(
        root_path=request.root_path
    ).first()
    if existing:
        session.close()
        raise HTTPException(
            status_code=409,
            detail=f"Folder is already being monitored: {request.root_path}"
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

    result = MonitoredFolderResponse(
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
    session.close()

    # Auto-sync in background
    background_tasks.add_task(
        _run_sync,
        folder_id,
        request.generate_document_summaries,
        request.generate_image_descriptions,
        request.extract_media_transcriptions
    )

    return result


@router.get("", response_model=List[MonitoredFolderResponse])
async def list_folders():
    """List all monitored folders."""
    session = get_session()

    folders = session.query(MonitoredFolderTable).order_by(
        MonitoredFolderTable.created_at.desc()
    ).all()

    result = [
        MonitoredFolderResponse(
            id=f.id,
            root_path=f.root_path,
            name=f.name,
            status=FolderStatus(f.status),
            last_synced_at=f.last_synced_at,
            last_llm_model=f.last_llm_model,
            total_files=f.total_files,
            processed_files=f.processed_files,
            failed_files=f.failed_files,
            generate_document_summaries=f.generate_document_summaries,
            generate_image_descriptions=f.generate_image_descriptions,
            extract_media_transcriptions=f.extract_media_transcriptions,
            ignore_patterns=f.ignore_patterns or [],
            created_at=f.created_at,
        )
        for f in folders
    ]

    session.close()
    return result


@router.get("/{folder_id}", response_model=MonitoredFolderResponse)
async def get_folder(folder_id: str):
    """Get details of a specific monitored folder."""
    session = get_session()

    folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
    if not folder:
        session.close()
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

    result = MonitoredFolderResponse(
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

    session.close()
    return result


@router.delete("/{folder_id}")
async def delete_folder(folder_id: str):
    """Remove a folder from monitoring.

    This only removes the folder from the app's database.
    The actual files on disk are NOT deleted.
    """
    session = get_session()

    folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
    if not folder:
        session.close()
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

    # Delete folder (cascade deletes files due to relationship)
    session.delete(folder)
    session.commit()
    session.close()

    return {"message": "Folder removed from monitoring", "folder_id": folder_id}


@router.post("/{folder_id}/sync", response_model=MonitoredFolderResponse)
async def sync_folder(
    folder_id: str,
    request: Optional[FolderSyncRequest] = None,
    background_tasks: BackgroundTasks = None
):
    """Sync a folder - detect and process new/modified/deleted files."""
    session = get_session()

    folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
    if not folder:
        session.close()
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

    if folder.status == FolderStatus.SYNCING.value:
        session.close()
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

    result = MonitoredFolderResponse(
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
    session.close()

    # Start sync in background
    background_tasks.add_task(
        _run_sync,
        folder_id,
        generate_document_summaries,
        generate_image_descriptions,
        extract_media_transcriptions
    )

    return result


@router.post("/{folder_id}/cancel")
async def cancel_sync(folder_id: str):
    """Cancel an ongoing sync operation."""
    session = get_session()

    folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
    if not folder:
        session.close()
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")

    if folder.status == FolderStatus.SYNCING.value:
        folder.status = FolderStatus.CANCELLED.value
        session.commit()

    session.close()
    return {"folder_id": folder_id, "status": "cancelled"}
