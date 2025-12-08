"""Files API endpoints for v1.2 - file browsing and filtering."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from filevyasa.db.connection import get_session
from filevyasa.db.tables import FileObjectTable
from filevyasa.models.enums import ExtractionStatus

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
    llm_model: Optional[str]
    extraction_status: str
    extraction_error: Optional[str]
    is_password_protected: bool

    last_extracted_at: Optional[str]
    last_ai_processed_at: Optional[str]
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


def _build_file_response(file_obj: FileObjectTable) -> FileDetailResponse:
    """Build FileDetailResponse from a FileObjectTable instance."""
    def _to_iso(dt):
        """Convert datetime to ISO string, preserving None."""
        return dt.isoformat() if dt else None

    path_parts = file_obj.path.rsplit("/", 1)
    parent_dir = path_parts[0] if len(path_parts) > 1 else ""

    return FileDetailResponse(
        id=file_obj.id,
        path=file_obj.path,
        filename=file_obj.filename,
        extension=file_obj.extension,
        mime_type=file_obj.mime_type,
        size_bytes=file_obj.size_bytes,
        size_human=_format_size(file_obj.size_bytes),
        created_at=_to_iso(file_obj.created_at),
        modified_at=_to_iso(file_obj.modified_at),
        accessed_at=_to_iso(file_obj.accessed_at),
        is_symlink=getattr(file_obj, 'is_symlink', False),
        category=file_obj.category,
        parent_dir=parent_dir,
        content_preview=file_obj.content_preview,
        exif_data=file_obj.exif_data or {},
        metadata=file_obj.file_metadata or {},
        ai_brief_summary=file_obj.ai_brief_summary,
        ai_summary=file_obj.ai_summary,
        llm_model=getattr(file_obj, 'llm_model', None),
        extraction_status=getattr(file_obj, 'extraction_status', 'pending'),
        extraction_error=getattr(file_obj, 'extraction_error', None),
        is_password_protected=getattr(file_obj, 'is_password_protected', False),
        last_extracted_at=_to_iso(getattr(file_obj, 'last_extracted_at', None)),
        last_ai_processed_at=_to_iso(getattr(file_obj, 'last_ai_processed_at', None)),
        scanned_at=_to_iso(getattr(file_obj, 'scanned_at', None)) or "",
        summarized_at=_to_iso(getattr(file_obj, 'summarized_at', None)),
    )


@router.get("/", response_model=FileListResponse)
async def list_files(
    folder_id: Optional[str] = Query(None, description="Filter by folder ID"),
    categories: Optional[str] = Query(None, description="Filter by categories (comma-separated)"),
    extraction_status: Optional[ExtractionStatus] = Query(None, description="Filter by extraction status"),
    extension: Optional[str] = Query(None, description="Filter by extension"),
    search: Optional[str] = Query(None, description="Search in filename"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
):
    """List files with optional filtering."""
    session = get_session()

    query = session.query(FileObjectTable)

    # Apply filters
    if folder_id:
        query = query.filter(FileObjectTable.folder_id == folder_id)
    
    if categories:
        category_list = [c.strip() for c in categories.split(",") if c.strip()]
        if category_list:
            query = query.filter(FileObjectTable.category.in_(category_list))
    
    if extraction_status:
        query = query.filter(FileObjectTable.extraction_status == extraction_status.value)
    
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


@router.get("/lookup", response_model=FileDetailResponse)
async def lookup_file(
    id: Optional[str] = Query(None, description="Lookup by file ID"),
    path: Optional[str] = Query(None, description="Lookup by file path"),
    inode: Optional[int] = Query(None, description="Lookup by inode"),
):
    """Get file by ID, path, or inode. Exactly one parameter must be provided."""
    params_provided = sum(p is not None for p in [id, path, inode])
    if params_provided != 1:
        raise HTTPException(
            status_code=400,
            detail="Exactly one of 'id', 'path', or 'inode' must be provided",
        )

    session = get_session()
    try:
        if id is not None:
            file_obj = session.query(FileObjectTable).filter_by(id=id).first()
            lookup_desc = f"id: {id}"
        elif path is not None:
            file_obj = session.query(FileObjectTable).filter_by(path=path).first()
            lookup_desc = f"path: {path}"
        else:
            file_obj = session.query(FileObjectTable).filter_by(inode=inode).first()
            lookup_desc = f"inode: {inode}"

        if not file_obj:
            raise HTTPException(status_code=404, detail=f"File not found ({lookup_desc})")

        return _build_file_response(file_obj)
    finally:
        session.close()


@router.get("/{file_id}", response_model=FileDetailResponse)
async def get_file(file_id: str):
    """Get detailed information about a specific file by ID."""
    session = get_session()
    try:
        file_obj = session.query(FileObjectTable).filter_by(id=file_id).first()
        if not file_obj:
            raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
        return _build_file_response(file_obj)
    finally:
        session.close()
