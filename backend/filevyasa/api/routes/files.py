"""Files API endpoints for v1.2 - file browsing and filtering."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from filevyasa.db.connection import get_session
from filevyasa.db.tables import FileObjectTable
from filevyasa.models.enums import FileCategory

router = APIRouter()


class FileListResponse(BaseModel):
    """Response for file list queries."""
    
    total: int
    page: int
    page_size: int
    files: List[dict]


class FileDetailResponse(BaseModel):
    """Detailed file response."""
    
    id: str
    path: str
    filename: str
    extension: str
    mime_type: str
    size_bytes: int
    size_human: str
    created_at: Optional[str]
    modified_at: Optional[str]
    accessed_at: Optional[str]
    is_symlink: bool
    category: str
    parent_dir: str
    content_preview: str
    exif_data: dict
    metadata: dict
    ai_brief_summary: str
    ai_summary: str
    extraction_status: str
    extraction_error: Optional[str]
    is_password_protected: bool
    scanned_at: str
    summarized_at: Optional[str]


def _format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    size = size_bytes
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


@router.get("/", response_model=FileListResponse)
async def list_files(
    scan_id: Optional[str] = Query(None, description="Filter by scan ID"),
    category: Optional[FileCategory] = Query(None, description="Filter by file category"),
    extension: Optional[str] = Query(None, description="Filter by extension"),
    search: Optional[str] = Query(None, description="Search in filename"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
):
    """List files with optional filtering."""
    session = get_session()
    
    query = session.query(FileObjectTable)
    
    # Apply filters
    if scan_id:
        query = query.filter(FileObjectTable.scan_id == scan_id)
    if category:
        query = query.filter(FileObjectTable.category == category.value)
    if extension:
        query = query.filter(FileObjectTable.extension == extension.lower())
    if search:
        query = query.filter(FileObjectTable.filename.ilike(f"%{search}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    files = query.offset(offset).limit(page_size).all()
    
    result_files = []
    for f in files:
        result_files.append({
            "id": f.id,
            "path": f.path,
            "filename": f.filename,
            "extension": f.extension,
            "mime_type": f.mime_type,
            "size_bytes": f.size_bytes,
            "size_human": _format_size(f.size_bytes),
            "category": f.category,
            "ai_brief_summary": f.ai_brief_summary,
            "scanned_at": f.scanned_at.isoformat() if f.scanned_at else None,
        })
    
    session.close()
    
    return FileListResponse(
        total=total,
        page=page,
        page_size=page_size,
        files=result_files,
    )


@router.get("/{file_id}", response_model=FileDetailResponse)
async def get_file(file_id: str):
    """Get detailed information about a specific file."""
    session = get_session()
    
    file_obj = session.query(FileObjectTable).filter_by(id=file_id).first()
    if not file_obj:
        session.close()
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    
    # Calculate parent dir
    path_parts = file_obj.path.rsplit("/", 1)
    parent_dir = path_parts[0] if len(path_parts) > 1 else ""
    
    result = FileDetailResponse(
        id=file_obj.id,
        path=file_obj.path,
        filename=file_obj.filename,
        extension=file_obj.extension,
        mime_type=file_obj.mime_type,
        size_bytes=file_obj.size_bytes,
        size_human=_format_size(file_obj.size_bytes),
        created_at=file_obj.created_at.isoformat() if file_obj.created_at else None,
        modified_at=file_obj.modified_at.isoformat() if file_obj.modified_at else None,
        accessed_at=file_obj.accessed_at.isoformat() if getattr(file_obj, 'accessed_at', None) else None,
        is_symlink=getattr(file_obj, 'is_symlink', False),
        category=file_obj.category,
        parent_dir=parent_dir,
        content_preview=file_obj.content_preview,
        exif_data=file_obj.exif_data or {},
        metadata=file_obj.file_metadata or {},
        ai_brief_summary=file_obj.ai_brief_summary,
        ai_summary=file_obj.ai_summary,
        extraction_status=getattr(file_obj, 'extraction_status', 'pending'),
        extraction_error=getattr(file_obj, 'extraction_error', None),
        is_password_protected=getattr(file_obj, 'is_password_protected', False),
        scanned_at=file_obj.scanned_at.isoformat() if file_obj.scanned_at else "",
        summarized_at=file_obj.summarized_at.isoformat() if file_obj.summarized_at else None,
    )
    
    session.close()
    return result


@router.get("/categories/stats")
async def get_category_stats(scan_id: Optional[str] = None):
    """Get statistics by file category."""
    session = get_session()
    
    from sqlalchemy import func
    
    query = session.query(
        FileObjectTable.category,
        func.count(FileObjectTable.id).label("count"),
        func.sum(FileObjectTable.size_bytes).label("total_size"),
    ).group_by(FileObjectTable.category)
    
    if scan_id:
        query = query.filter(FileObjectTable.scan_id == scan_id)
    
    results = query.all()
    
    stats = {}
    for category, count, total_size in results:
        stats[category] = {
            "count": count,
            "total_size": total_size or 0,
            "total_size_human": _format_size(total_size or 0),
        }
    
    session.close()
    return stats


@router.get("/extensions/stats")
async def get_extension_stats(scan_id: Optional[str] = None, limit: int = 20):
    """Get statistics by file extension."""
    session = get_session()
    
    from sqlalchemy import func
    
    query = session.query(
        FileObjectTable.extension,
        func.count(FileObjectTable.id).label("count"),
    ).group_by(FileObjectTable.extension).order_by(
        func.count(FileObjectTable.id).desc()
    ).limit(limit)
    
    if scan_id:
        query = query.filter(FileObjectTable.scan_id == scan_id)
    
    results = query.all()
    
    stats = [{"extension": ext or "(no extension)", "count": count} for ext, count in results]
    
    session.close()
    return stats
