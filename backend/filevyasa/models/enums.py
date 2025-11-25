"""Enumeration types for FileVyasa."""

from enum import Enum


class FileCategory(str, Enum):
    """High-level file category for organization."""
    
    DOCUMENT = "document"       # PDFs, DOCX, ODT, RTF, etc.
    SPREADSHEET = "spreadsheet" # XLSX, CSV, ODS
    PRESENTATION = "presentation"  # PPTX, KEY, ODP
    IMAGE = "image"             # PNG, JPG, GIF, etc.
    VIDEO = "video"             # MP4, MOV, AVI, MKV
    AUDIO = "audio"             # MP3, WAV, M4A
    ARCHIVE = "archive"         # ZIP, TAR, GZ
    CODE = "code"               # PY, JS, etc.
    TEXT = "text"               # TXT, MD
    OTHER = "other"             # Unknown/unclassified


class FolderStatus(str, Enum):
    """Status of a monitored folder's sync operation."""
    
    IDLE = "idle"              # Not currently syncing
    SYNCING = "syncing"        # Sync in progress
    CANCELLED = "cancelled"    # Sync was cancelled
    ERROR = "error"            # Sync failed with error


class ActionType(str, Enum):
    """Type of file operation action (for v1.4+)."""
    
    MOVE = "move"
    RENAME = "rename"
    COPY = "copy"


class ApprovalStatus(str, Enum):
    """Approval status for planned actions (for v1.4+)."""
    
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ExtractionStatus(str, Enum):
    """Status of content extraction for a file."""
    
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
