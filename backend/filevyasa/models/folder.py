"""MonitoredFolder model representing a folder being tracked by FileVyasa."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from filevyasa.models.enums import FolderStatus


class MonitoredFolderBase(BaseModel):
    """Base attributes for a monitored folder."""

    root_path: str = Field(..., description="Absolute path to the monitored folder")
    name: str = Field(..., description="Display name (typically folder basename)")
    # AI processing options
    generate_document_summaries: bool = Field(
        default=True, description="Generate AI summaries for documents"
    )
    generate_image_descriptions: bool = Field(
        default=True, description="Generate AI descriptions for images"
    )
    extract_media_transcriptions: bool = Field(
        default=True, description="Extract transcriptions from audio/video"
    )
    ignore_patterns: list[str] = Field(
        default_factory=list, description="Patterns to ignore during sync"
    )


class MonitoredFolderCreate(BaseModel):
    """Schema for creating a new monitored folder."""

    root_path: str = Field(..., description="Absolute path to the folder to monitor")
    # AI processing options
    generate_document_summaries: bool = Field(
        default=True, description="Generate AI summaries for documents"
    )
    generate_image_descriptions: bool = Field(
        default=True, description="Generate AI descriptions for images"
    )
    extract_media_transcriptions: bool = Field(
        default=True, description="Extract transcriptions from audio/video"
    )
    ignore_patterns: Optional[list[str]] = Field(
        default=None, description="Additional patterns to ignore"
    )


class MonitoredFolder(MonitoredFolderBase):
    """Full MonitoredFolder with database fields."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")

    # Sync state
    status: FolderStatus = Field(
        default=FolderStatus.IDLE, description="Current sync status"
    )
    last_sync_started_at: Optional[datetime] = Field(
        default=None, description="When the current/last sync was started"
    )
    last_synced_at: Optional[datetime] = Field(
        default=None, description="When folder was last synced"
    )
    last_llm_model: Optional[str] = Field(
        default=None, description="LLM model used in last sync"
    )

    # Stats
    total_files: int = Field(default=0, description="Total files in folder")
    processed_files: int = Field(default=0, description="Files processed in current/last sync")
    failed_files: int = Field(default=0, description="Files that failed processing")
    skipped_files: int = Field(default=0, description="System files skipped during scan")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="When folder was added")

    model_config = ConfigDict(from_attributes=True)


class MonitoredFolderResponse(BaseModel):
    """API response model for MonitoredFolder."""

    id: str
    root_path: str
    name: str

    status: FolderStatus
    last_synced_at: Optional[datetime]
    last_llm_model: Optional[str]
    last_sync_started_at: Optional[datetime]

    total_files: int
    processed_files: int
    failed_files: int
    skipped_files: int

    # AI processing options
    generate_document_summaries: bool
    generate_image_descriptions: bool
    extract_media_transcriptions: bool
    ignore_patterns: list[str]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FolderSyncRequest(BaseModel):
    """Request to sync a folder."""

    generate_document_summaries: Optional[bool] = Field(
        default=None,
        description="Override folder's generate_document_summaries setting for this sync"
    )
    generate_image_descriptions: Optional[bool] = Field(
        default=None,
        description="Override folder's generate_image_descriptions setting for this sync"
    )
    extract_media_transcriptions: Optional[bool] = Field(
        default=None,
        description="Override folder's extract_media_transcriptions setting for this sync"
    )


class FolderSyncStatus(BaseModel):
    """Status response during folder sync."""

    folder_id: str
    status: FolderStatus
    total_files: int
    processed_files: int
    failed_files: int
    skipped_files: int = Field(default=0, description="System files skipped during scan")

    # Sync details
    new_files: int = Field(default=0, description="New files detected")
    modified_files: int = Field(default=0, description="Modified files detected")
    deleted_files: int = Field(default=0, description="Files removed from disk")
    unchanged_files: int = Field(default=0, description="Files skipped (unchanged)")
