"""MonitoredFolder model representing a folder being tracked by FileVyasa."""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from filevyasa.models.enums import FolderStatus


class MonitoredFolderBase(BaseModel):
    """Base attributes for a monitored folder."""
    
    root_path: str = Field(..., description="Absolute path to the monitored folder")
    name: str = Field(..., description="Display name (typically folder basename)")
    generate_summaries: bool = Field(default=True, description="Whether to generate AI summaries")
    ignore_patterns: list[str] = Field(default_factory=list, description="Patterns to ignore during sync")


class MonitoredFolderCreate(BaseModel):
    """Schema for creating a new monitored folder."""
    
    root_path: str = Field(..., description="Absolute path to the folder to monitor")
    generate_summaries: bool = Field(default=True, description="Whether to generate AI summaries")
    ignore_patterns: Optional[list[str]] = Field(default=None, description="Additional patterns to ignore")


class MonitoredFolder(MonitoredFolderBase):
    """Full MonitoredFolder with database fields."""
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    
    # Sync state
    status: FolderStatus = Field(default=FolderStatus.IDLE, description="Current sync status")
    last_synced_at: Optional[datetime] = Field(default=None, description="When folder was last synced")
    last_llm_model: Optional[str] = Field(default=None, description="LLM model used in last sync")
    
    # Stats
    total_files: int = Field(default=0, description="Total files in folder")
    processed_files: int = Field(default=0, description="Files processed in current/last sync")
    failed_files: int = Field(default=0, description="Files that failed processing")
    
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
    
    total_files: int
    processed_files: int
    failed_files: int
    
    generate_summaries: bool
    ignore_patterns: list[str]
    
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FolderSyncRequest(BaseModel):
    """Request to sync a folder."""
    
    generate_summaries: Optional[bool] = Field(
        default=None, 
        description="Override folder's generate_summaries setting for this sync"
    )


class FolderSyncStatus(BaseModel):
    """Status response during folder sync."""
    
    folder_id: str
    status: FolderStatus
    total_files: int
    processed_files: int
    failed_files: int
    
    # Sync details
    new_files: int = Field(default=0, description="New files detected")
    modified_files: int = Field(default=0, description="Modified files detected")
    deleted_files: int = Field(default=0, description="Files removed from disk")
    unchanged_files: int = Field(default=0, description="Files skipped (unchanged)")
