"""SQLAlchemy table definitions for FileVyasa."""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class MonitoredFolderTable(Base):
    """Table for tracking monitored folders.

    Each folder can only be added once (unique root_path).
    Files belong to folders, not scans.
    """

    __tablename__ = "monitored_folders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    root_path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)  # Display name (folder basename)

    # Sync state (idle, syncing, cancelled, error)
    status: Mapped[str] = mapped_column(String(20), default="idle")
    last_sync_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_llm_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Stats
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    processed_files: Mapped[int] = mapped_column(Integer, default=0)
    failed_files: Mapped[int] = mapped_column(Integer, default=0)

    # Settings per folder - AI processing options
    generate_document_summaries: Mapped[bool] = mapped_column(Boolean, default=True)
    generate_image_descriptions: Mapped[bool] = mapped_column(Boolean, default=True)
    extract_media_transcriptions: Mapped[bool] = mapped_column(Boolean, default=True)
    ignore_patterns: Mapped[dict] = mapped_column(JSON, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationship to files
    files: Mapped[list["FileObjectTable"]] = relationship(
        "FileObjectTable", back_populates="folder", cascade="all, delete-orphan"
    )


class FileObjectTable(Base):
    """Table for storing scanned file objects."""

    __tablename__ = "file_objects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    folder_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("monitored_folders.id"), nullable=True
    )

    # File identification
    path: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    extension: Mapped[str] = mapped_column(String(32), default="")
    mime_type: Mapped[str] = mapped_column(String(128), default="")
    # Inode for tracking files across renames/moves
    # Cross-platform: Unix st_ino, Windows file index
    # Note: Inode can be reused after file deletion, but rare and acceptable
    inode: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)

    # File attributes
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    modified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    is_symlink: Mapped[bool] = mapped_column(Boolean, default=False)

    # Classification
    category: Mapped[str] = mapped_column(String(32), default="other")

    # Content
    content_preview: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Metadata as JSON
    exif_data: Mapped[dict] = mapped_column(JSON, default=dict)
    file_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # AI summaries
    ai_brief_summary: Mapped[str] = mapped_column(Text, default="")
    ai_summary: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # AI-suggested filename improvements
    suggested_filename: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    filename_quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Extraction status
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")
    extraction_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_password_protected: Mapped[bool] = mapped_column(Boolean, default=False)

    # Processing timestamps
    last_extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_ai_processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    scanned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    summarized_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship to folder
    folder: Mapped[Optional["MonitoredFolderTable"]] = relationship(
        "MonitoredFolderTable", back_populates="files"
    )
