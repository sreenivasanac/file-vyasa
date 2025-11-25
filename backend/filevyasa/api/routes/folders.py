"""Folder API endpoints for managing monitored folders and sync operations."""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from filevyasa.config import settings
from filevyasa.db.connection import get_session
from filevyasa.db.tables import MonitoredFolderTable, FileObjectTable
from filevyasa.extractor import enrich_file_object
from filevyasa.llm import Summarizer
from filevyasa.models.file_object import FileObject, FileObjectResponse
from filevyasa.models.folder import (
    MonitoredFolderCreate,
    MonitoredFolderResponse,
    FolderSyncRequest,
    FolderSyncStatus,
)
from filevyasa.models.enums import FolderStatus
from filevyasa.scanner import Scanner

router = APIRouter()


# --- Helper Functions ---

def _get_current_llm_model() -> str:
    """Get the currently configured LLM model string."""
    return f"{settings.llm_provider}/{settings.llm_model}"


def _check_folder_conflicts(root_path: str, exclude_folder_id: Optional[str] = None) -> Optional[str]:
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
    generate_summaries: bool,
):
    """Background task to sync a folder.
    
    Sync logic:
    - New files: full extract + summarize
    - Modified files (modified_at changed): re-extract + re-summarize
    - Model changed: re-summarize only (if generate_summaries enabled)
    - Unchanged: skip
    - Deleted from disk: remove from DB
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
        summarizer = Summarizer() if generate_summaries else None
        
        # Get existing files from DB indexed by path
        existing_files = {
            f.path: f for f in session.query(FileObjectTable).filter_by(folder_id=folder_id).all()
        }
        
        # Scan filesystem
        scanner = Scanner(
            ignore_patterns=list(folder.ignore_patterns or []) + list(settings.default_ignore_patterns),
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
                    
                    is_non_content_file = (
                        file_obj.content_preview and
                        file_obj.metadata.get("extraction_method") == "skipped"
                    )
                    
                    if is_non_content_file:
                        file_obj.ai_brief_summary = file_obj.content_preview
                        file_obj.ai_summary = file_obj.content_preview
                        file_obj.llm_model = None
                        file_obj.summarized_at = datetime.now()
                    elif summarizer and file_obj.content_preview:
                        file_obj = summarizer.summarize(file_obj)
                    
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
                        category=file_obj.category.value,
                        content_preview=file_obj.content_preview,
                        exif_data=file_obj.exif_data,
                        file_metadata=file_obj.metadata,
                        ai_brief_summary=file_obj.ai_brief_summary,
                        ai_summary=file_obj.ai_summary,
                        llm_model=getattr(file_obj, 'llm_model', None),
                        extraction_status=getattr(file_obj, 'extraction_status', 'pending').value if hasattr(getattr(file_obj, 'extraction_status', None), 'value') else str(getattr(file_obj, 'extraction_status', 'pending')),
                        extraction_error=getattr(file_obj, 'extraction_error', None),
                        is_password_protected=getattr(file_obj, 'is_password_protected', False),
                        scanned_at=file_obj.scanned_at,
                        summarized_at=file_obj.summarized_at,
                    )
                    session.add(new_db_file)
                    
                elif file_obj.modified_at and db_file.modified_at and file_obj.modified_at > db_file.modified_at:
                    # MODIFIED - re-extract + re-summarize
                    modified_count += 1
                    file_obj = enrich_file_object(file_obj)
                    
                    is_non_content_file = (
                        file_obj.content_preview and
                        file_obj.metadata.get("extraction_method") == "skipped"
                    )
                    
                    if is_non_content_file:
                        file_obj.ai_brief_summary = file_obj.content_preview
                        file_obj.ai_summary = file_obj.content_preview
                        file_obj.llm_model = None
                        file_obj.summarized_at = datetime.now()
                    elif summarizer and file_obj.content_preview:
                        file_obj = summarizer.summarize(file_obj)
                    
                    # Update existing file
                    db_file.size_bytes = file_obj.size_bytes
                    db_file.modified_at = file_obj.modified_at
                    db_file.accessed_at = getattr(file_obj, 'accessed_at', None)
                    db_file.content_preview = file_obj.content_preview
                    db_file.exif_data = file_obj.exif_data
                    db_file.file_metadata = file_obj.metadata
                    db_file.ai_brief_summary = file_obj.ai_brief_summary
                    db_file.ai_summary = file_obj.ai_summary
                    db_file.llm_model = getattr(file_obj, 'llm_model', None)
                    db_file.extraction_status = getattr(file_obj, 'extraction_status', 'pending').value if hasattr(getattr(file_obj, 'extraction_status', None), 'value') else str(getattr(file_obj, 'extraction_status', 'pending'))
                    db_file.extraction_error = getattr(file_obj, 'extraction_error', None)
                    db_file.scanned_at = datetime.now()
                    db_file.summarized_at = file_obj.summarized_at
                    
                elif generate_summaries and db_file.llm_model != current_model:
                    # MODEL CHANGED - re-summarize only (skip extraction)
                    modified_count += 1
                    
                    # Create a temporary file object with existing content
                    temp_file_obj = FileObject(
                        id=db_file.id,
                        folder_id=folder_id,
                        path=db_file.path,
                        filename=db_file.filename,
                        extension=db_file.extension,
                        mime_type=db_file.mime_type,
                        size_bytes=db_file.size_bytes,
                        created_at=db_file.created_at,
                        modified_at=db_file.modified_at,
                        category=db_file.category,
                        content_preview=db_file.content_preview,
                        exif_data=db_file.exif_data or {},
                        metadata=db_file.file_metadata or {},
                    )
                    
                    # Only re-summarize if we have content and it's not a non-content file
                    is_non_content_file = (
                        db_file.content_preview and
                        (db_file.file_metadata or {}).get("extraction_method") == "skipped"
                    )
                    
                    if not is_non_content_file and summarizer and db_file.content_preview:
                        temp_file_obj = summarizer.summarize(temp_file_obj)
                        db_file.ai_brief_summary = temp_file_obj.ai_brief_summary
                        db_file.ai_summary = temp_file_obj.ai_summary
                        db_file.llm_model = temp_file_obj.llm_model
                        db_file.summarized_at = temp_file_obj.summarized_at
                    
                else:
                    # UNCHANGED - skip
                    unchanged_count += 1
                    continue  # Don't count as processed
                
                session.commit()
                processed += 1
                
            except Exception as e:
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
            folder.last_llm_model = current_model if generate_summaries else folder.last_llm_model
        
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


# --- API Endpoints ---

@router.post("", response_model=MonitoredFolderResponse)
async def add_folder(request: MonitoredFolderCreate, background_tasks: BackgroundTasks):
    """Add a new folder to monitor. Auto-syncs after adding.
    
    Validates:
    - Path exists and is a directory
    - Path is not already monitored
    - Path does not conflict with existing folders (no nesting)
    """
    # Validate path exists
    if not os.path.exists(request.root_path):
        raise HTTPException(status_code=400, detail=f"Path does not exist: {request.root_path}")
    if not os.path.isdir(request.root_path):
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.root_path}")
    
    # Check for conflicts with existing folders
    conflict = _check_folder_conflicts(request.root_path)
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"This folder conflicts with an existing monitored folder: {conflict}. Please remove one of the folders first."
        )
    
    session = get_session()
    
    # Check if already exists
    existing = session.query(MonitoredFolderTable).filter_by(root_path=request.root_path).first()
    if existing:
        session.close()
        raise HTTPException(status_code=409, detail=f"Folder is already being monitored: {request.root_path}")
    
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
        generate_summaries=request.generate_summaries,
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
        generate_summaries=folder.generate_summaries,
        ignore_patterns=folder.ignore_patterns or [],
        created_at=folder.created_at,
    )
    session.close()
    
    # Auto-sync in background
    background_tasks.add_task(_run_sync, folder_id, request.generate_summaries)
    
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
            generate_summaries=f.generate_summaries,
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
        generate_summaries=folder.generate_summaries,
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
async def sync_folder(folder_id: str, request: Optional[FolderSyncRequest] = None, background_tasks: BackgroundTasks = None):
    """Sync a folder - detect and process new/modified/deleted files."""
    session = get_session()
    
    folder = session.query(MonitoredFolderTable).filter_by(id=folder_id).first()
    if not folder:
        session.close()
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_id}")
    
    if folder.status == FolderStatus.SYNCING.value:
        session.close()
        raise HTTPException(status_code=409, detail="Folder is already syncing")
    
    # Determine whether to generate summaries
    generate_summaries = folder.generate_summaries
    if request and request.generate_summaries is not None:
        generate_summaries = request.generate_summaries
    
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
        generate_summaries=folder.generate_summaries,
        ignore_patterns=folder.ignore_patterns or [],
        created_at=folder.created_at,
    )
    session.close()
    
    # Start sync in background
    background_tasks.add_task(_run_sync, folder_id, generate_summaries)
    
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
