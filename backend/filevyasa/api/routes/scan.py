"""Scan API endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from filevyasa.config import settings
from filevyasa.db.connection import get_session
from filevyasa.db.tables import ScanSessionTable, FileObjectTable
from filevyasa.extractor import enrich_file_object
from filevyasa.llm import Summarizer
from filevyasa.models.file_object import FileObject, FileObjectResponse
from filevyasa.models.enums import ScanStatus
from filevyasa.scanner import Scanner

router = APIRouter()


class ScanRequest(BaseModel):
    """Request to start a scan."""
    
    root_path: str = Field(..., description="Directory path to scan")
    recursive: bool = Field(default=True, description="Scan subdirectories")
    ignore_patterns: Optional[List[str]] = Field(
        default=None, description="Additional patterns to ignore"
    )
    generate_summaries: bool = Field(
        default=True, description="Generate AI summaries for files"
    )


class ScanResponse(BaseModel):
    """Response for scan operations."""
    
    scan_id: str
    root_path: str
    status: str
    total_files: int
    processed_files: int
    failed_files: int
    started_at: datetime
    completed_at: Optional[datetime] = None


class ScanStatusResponse(BaseModel):
    """Status response for a scan."""
    
    scan_id: str
    status: str
    total_files: int
    processed_files: int
    failed_files: int
    files: List[FileObjectResponse] = []


def _run_scan(
    scan_id: str,
    root_path: str,
    recursive: bool,
    ignore_patterns: List[str],
    generate_summaries: bool
):
    """Background task to run a scan."""
    session = get_session()
    
    try:
        # Update status to in_progress
        scan_session = session.query(ScanSessionTable).filter_by(id=scan_id).first()
        scan_session.status = ScanStatus.IN_PROGRESS.value
        session.commit()
        
        # Initialize scanner and summarizer
        scanner = Scanner(ignore_patterns=ignore_patterns, scan_id=scan_id)
        summarizer = Summarizer() if generate_summaries else None
        
        # Scan and process files
        files = scanner.scan_to_list(root_path, recursive)
        scan_session.total_files = len(files)
        session.commit()
        
        processed = 0
        failed = 0
        
        for file_obj in files:
            try:
                # Extract content
                file_obj = enrich_file_object(file_obj)
                
                # Check if this is a non-content file (from NonContentExtractor)
                # These have "file with name" in the content preview
                is_non_content_file = (
                    file_obj.content_preview and 
                    file_obj.metadata.get("extraction_method") == "skipped"
                )
                
                if is_non_content_file:
                    # Use content_preview as summary directly, skip LLM
                    file_obj.ai_brief_summary = file_obj.content_preview
                    file_obj.ai_summary = file_obj.content_preview
                    file_obj.summarized_at = datetime.now()
                elif summarizer and file_obj.content_preview:
                    # Generate LLM summary for content files
                    file_obj = summarizer.summarize(file_obj)
                
                # Save to database
                db_file = FileObjectTable(
                    id=file_obj.id,
                    scan_id=scan_id,
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
                    extraction_status=getattr(file_obj, 'extraction_status', 'pending').value if hasattr(getattr(file_obj, 'extraction_status', None), 'value') else str(getattr(file_obj, 'extraction_status', 'pending')),
                    extraction_error=getattr(file_obj, 'extraction_error', None),
                    is_password_protected=getattr(file_obj, 'is_password_protected', False),
                    scanned_at=file_obj.scanned_at,
                    summarized_at=file_obj.summarized_at,
                )
                session.add(db_file)
                session.commit()  # Commit each file immediately for real-time UI updates
                processed += 1
                
            except Exception as e:
                failed += 1
            
            # Update progress after each file
            scan_session.processed_files = processed
            scan_session.failed_files = failed
            session.commit()
        
        # Final update
        scan_session.status = ScanStatus.COMPLETED.value
        scan_session.processed_files = processed
        scan_session.failed_files = failed
        scan_session.completed_at = datetime.now()
        session.commit()
        
    except Exception as e:
        scan_session = session.query(ScanSessionTable).filter_by(id=scan_id).first()
        if scan_session:
            scan_session.status = ScanStatus.FAILED.value
            scan_session.completed_at = datetime.now()
            session.commit()
    finally:
        session.close()


@router.post("/start", response_model=ScanResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start a new scan of a directory."""
    import os
    
    # Validate path
    if not os.path.exists(request.root_path):
        raise HTTPException(status_code=400, detail=f"Path does not exist: {request.root_path}")
    if not os.path.isdir(request.root_path):
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.root_path}")
    
    # Combine ignore patterns
    ignore_patterns = list(settings.default_ignore_patterns)
    if request.ignore_patterns:
        ignore_patterns.extend(request.ignore_patterns)
    
    # Create scan session
    scan_id = str(uuid4())
    session = get_session()
    
    scan_session = ScanSessionTable(
        id=scan_id,
        root_path=request.root_path,
        status=ScanStatus.PENDING.value,
        ignore_patterns=ignore_patterns,
        started_at=datetime.now(),
    )
    session.add(scan_session)
    session.commit()
    session.close()
    
    # Start background scan
    background_tasks.add_task(
        _run_scan,
        scan_id,
        request.root_path,
        request.recursive,
        ignore_patterns,
        request.generate_summaries,
    )
    
    return ScanResponse(
        scan_id=scan_id,
        root_path=request.root_path,
        status=ScanStatus.PENDING.value,
        total_files=0,
        processed_files=0,
        failed_files=0,
        started_at=datetime.now(),
    )


@router.get("/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status(scan_id: str, include_files: bool = False):
    """Get the status of a scan."""
    session = get_session()
    
    scan_session = session.query(ScanSessionTable).filter_by(id=scan_id).first()
    if not scan_session:
        session.close()
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")
    
    files = []
    if include_files:
        db_files = session.query(FileObjectTable).filter_by(scan_id=scan_id).all()
        for f in db_files:
            files.append(FileObjectResponse(
                id=f.id,
                path=f.path,
                filename=f.filename,
                extension=f.extension,
                mime_type=f.mime_type,
                size_bytes=f.size_bytes,
                size_human=_format_size(f.size_bytes),
                created_at=f.created_at,
                modified_at=f.modified_at,
                accessed_at=getattr(f, 'accessed_at', None),
                is_symlink=getattr(f, 'is_symlink', False),
                category=f.category,
                parent_dir=str(f.path).rsplit("/", 1)[0] if "/" in f.path else "",
                ai_brief_summary=f.ai_brief_summary,
                ai_summary=f.ai_summary,
                exif_data=f.exif_data or {},
                metadata=f.file_metadata or {},
                extraction_status=getattr(f, 'extraction_status', 'pending'),
                extraction_error=getattr(f, 'extraction_error', None),
                is_password_protected=getattr(f, 'is_password_protected', False),
                scanned_at=f.scanned_at,
                summarized_at=f.summarized_at,
            ))
    
    session.close()
    
    return ScanStatusResponse(
        scan_id=scan_session.id,
        status=scan_session.status,
        total_files=scan_session.total_files,
        processed_files=scan_session.processed_files,
        failed_files=scan_session.failed_files,
        files=files,
    )


def _format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    size = size_bytes
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


@router.get("/recent", response_model=List[ScanResponse])
async def get_recent_scans(limit: int = 10):
    """Get recent scan sessions."""
    session = get_session()
    
    scans = session.query(ScanSessionTable).order_by(
        ScanSessionTable.started_at.desc()
    ).limit(limit).all()
    
    result = [
        ScanResponse(
            scan_id=s.id,
            root_path=s.root_path,
            status=s.status,
            total_files=s.total_files,
            processed_files=s.processed_files,
            failed_files=s.failed_files,
            started_at=s.started_at,
            completed_at=s.completed_at,
        )
        for s in scans
    ]
    
    session.close()
    return result
