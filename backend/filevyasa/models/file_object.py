"""FileObject model representing a scanned file with metadata and AI summaries."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field

from filevyasa.models.enums import ExtractionStatus, FileCategory


class FileObjectBase(BaseModel):
    """Base attributes for a file object."""

    path: str = Field(..., description="Absolute path to the file")
    filename: str = Field(..., description="File name with extension")
    extension: str = Field(default="", description="File extension (lowercase, without dot)")
    mime_type: str = Field(default="", description="MIME type of the file")

    size_bytes: int = Field(default=0, description="File size in bytes")
    created_at: Optional[datetime] = Field(default=None, description="File creation timestamp")
    modified_at: Optional[datetime] = Field(default=None, description="File modification timestamp")
    accessed_at: Optional[datetime] = Field(default=None, description="File last access timestamp")

    is_symlink: bool = Field(default=False, description="Whether file is a symbolic link")

    category: FileCategory = Field(
        default=FileCategory.OTHER, description="High-level file category"
    )

    # Extracted content (first N lines as markdown)
    content_preview: str = Field(default="", description="Extracted content preview (markdown)")

    # EXIF and file-specific metadata
    exif_data: dict[str, Any] = Field(default_factory=dict, description="EXIF metadata for images")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional file metadata")

    # AI-generated fields (v1.1)
    ai_brief_summary: str = Field(default="", description="AI-generated brief summary (~2 lines)")
    ai_summary: str = Field(default="", description="AI-generated detailed summary (~4 lines)")
    llm_model: Optional[str] = Field(
        default=None, description="LLM model used for summarization"
    )

    # Transcription for audio/video files
    transcription: Optional[str] = Field(
        default=None, description="Transcription text for audio/video files"
    )
    transcription_duration: Optional[float] = Field(
        default=None, description="Duration of transcribed content in seconds"
    )

    # Extraction status
    extraction_status: ExtractionStatus = Field(
        default=ExtractionStatus.PENDING, description="Content extraction status"
    )
    extraction_error: Optional[str] = Field(
        default=None, description="Error message if extraction failed"
    )
    is_password_protected: bool = Field(
        default=False, description="Whether file is password protected"
    )


class FileObjectCreate(FileObjectBase):
    """Schema for creating a new FileObject."""
    pass


class FileObject(FileObjectBase):
    """Full FileObject with database fields."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    folder_id: Optional[str] = Field(default=None, description="ID of the monitored folder")

    # Content hash for duplicate detection (v1.5)
    content_hash: Optional[str] = Field(default=None, description="SHA-256 hash of file content")

    # Processing timestamps
    scanned_at: datetime = Field(
        default_factory=datetime.now, description="When file was scanned"
    )
    summarized_at: Optional[datetime] = Field(
        default=None, description="When AI summary was generated"
    )

    @computed_field
    @property
    def size_human(self) -> str:
        """Human-readable file size."""
        size = self.size_bytes
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @computed_field
    @property
    def parent_dir(self) -> str:
        """Parent directory path."""
        return str(Path(self.path).parent)

    model_config = ConfigDict(from_attributes=True)


class FileObjectResponse(BaseModel):
    """API response model for FileObject."""

    id: str
    path: str
    filename: str
    extension: str
    mime_type: str
    size_bytes: int
    size_human: str
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
    accessed_at: Optional[datetime]
    is_symlink: bool
    category: FileCategory
    parent_dir: str

    ai_brief_summary: str
    ai_summary: str
    llm_model: Optional[str]

    # Transcription for audio/video files
    transcription: Optional[str]
    transcription_duration: Optional[float]

    exif_data: dict[str, Any]
    metadata: dict[str, Any]

    extraction_status: ExtractionStatus
    extraction_error: Optional[str]
    is_password_protected: bool

    scanned_at: datetime
    summarized_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
