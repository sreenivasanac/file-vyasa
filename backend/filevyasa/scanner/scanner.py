"""Directory scanner for file discovery."""

import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional
from uuid import uuid4

import structlog

from filevyasa.config import settings
from filevyasa.models.enums import FileCategory
from filevyasa.models.file_object import FileObject
from filevyasa.scanner.file_filter import FileFilter

logger = structlog.get_logger()


# Extension to category mapping
EXTENSION_CATEGORY_MAP = {
    # Documents
    "pdf": FileCategory.DOCUMENT,
    "doc": FileCategory.DOCUMENT,
    "docx": FileCategory.DOCUMENT,
    "odt": FileCategory.DOCUMENT,
    "rtf": FileCategory.DOCUMENT,
    "pages": FileCategory.DOCUMENT,
    
    # Text
    "txt": FileCategory.TEXT,
    "md": FileCategory.TEXT,
    "markdown": FileCategory.TEXT,
    
    # Spreadsheets
    "xlsx": FileCategory.SPREADSHEET,
    "xls": FileCategory.SPREADSHEET,
    "csv": FileCategory.SPREADSHEET,
    "ods": FileCategory.SPREADSHEET,
    "numbers": FileCategory.SPREADSHEET,
    
    # Presentations
    "pptx": FileCategory.PRESENTATION,
    "ppt": FileCategory.PRESENTATION,
    "key": FileCategory.PRESENTATION,
    "odp": FileCategory.PRESENTATION,
    
    # Images
    "png": FileCategory.IMAGE,
    "jpg": FileCategory.IMAGE,
    "jpeg": FileCategory.IMAGE,
    "gif": FileCategory.IMAGE,
    "bmp": FileCategory.IMAGE,
    "tiff": FileCategory.IMAGE,
    "tif": FileCategory.IMAGE,
    "webp": FileCategory.IMAGE,
    "heic": FileCategory.IMAGE,
    "heif": FileCategory.IMAGE,
    "svg": FileCategory.IMAGE,
    "ico": FileCategory.IMAGE,
    "psd": FileCategory.IMAGE,
    
    # Video
    "mp4": FileCategory.VIDEO,
    "mov": FileCategory.VIDEO,
    "avi": FileCategory.VIDEO,
    "mkv": FileCategory.VIDEO,
    "wmv": FileCategory.VIDEO,
    "flv": FileCategory.VIDEO,
    "m4v": FileCategory.VIDEO,
    "webm": FileCategory.VIDEO,
    
    # Audio
    "mp3": FileCategory.AUDIO,
    "wav": FileCategory.AUDIO,
    "m4a": FileCategory.AUDIO,
    "flac": FileCategory.AUDIO,
    "aac": FileCategory.AUDIO,
    "ogg": FileCategory.AUDIO,
    "wma": FileCategory.AUDIO,
    
    # Archives
    "zip": FileCategory.ARCHIVE,
    "tar": FileCategory.ARCHIVE,
    "gz": FileCategory.ARCHIVE,
    "rar": FileCategory.ARCHIVE,
    "7z": FileCategory.ARCHIVE,
    
    # Code
    "py": FileCategory.CODE,
    "js": FileCategory.CODE,
    "ts": FileCategory.CODE,
    "java": FileCategory.CODE,
    "c": FileCategory.CODE,
    "cpp": FileCategory.CODE,
    "h": FileCategory.CODE,
    "cs": FileCategory.CODE,
    "go": FileCategory.CODE,
    "rs": FileCategory.CODE,
    "rb": FileCategory.CODE,
    "php": FileCategory.CODE,
    "swift": FileCategory.CODE,
    "kt": FileCategory.CODE,
    "html": FileCategory.CODE,
    "css": FileCategory.CODE,
    "json": FileCategory.CODE,
    "yaml": FileCategory.CODE,
    "yml": FileCategory.CODE,
    "xml": FileCategory.CODE,
    "sql": FileCategory.CODE,
    "sh": FileCategory.CODE,
}


def get_file_category(extension: str) -> FileCategory:
    """Get the file category based on extension."""
    ext = extension.lower().lstrip(".")
    return EXTENSION_CATEGORY_MAP.get(ext, FileCategory.OTHER)


class Scanner:
    """Directory scanner for discovering and cataloging files."""
    
    def __init__(
        self,
        ignore_patterns: List[str] | None = None,
        folder_id: str | None = None
    ):
        """
        Initialize the scanner.
        
        Args:
            ignore_patterns: Patterns to ignore (defaults to config patterns)
            folder_id: Optional folder ID for associating scanned files
        """
        patterns = ignore_patterns or settings.default_ignore_patterns
        self.file_filter = FileFilter(patterns)
        self.folder_id = folder_id or str(uuid4())
    
    def scan_directory(
        self,
        root_path: str | Path,
        recursive: bool = True
    ) -> Generator[FileObject, None, None]:
        """
        Scan a directory and yield FileObject instances.
        
        Args:
            root_path: Root directory to scan
            recursive: Whether to scan subdirectories
            
        Yields:
            FileObject for each discovered file
        """
        root = Path(root_path).resolve()
        
        if not root.exists():
            raise ValueError(f"Directory does not exist: {root}")
        if not root.is_dir():
            raise ValueError(f"Path is not a directory: {root}")
        
        logger.info("starting_scan", root=str(root), recursive=recursive)
        
        if recursive:
            file_iterator = root.rglob("*")
        else:
            file_iterator = root.glob("*")
        
        for file_path in file_iterator:
            # Skip directories
            if file_path.is_dir():
                continue
            
            # Skip ignored files
            if self.file_filter.should_ignore(file_path):
                logger.debug("skipping_ignored_file", path=str(file_path))
                continue
            
            try:
                file_obj = self._create_file_object(file_path)
                yield file_obj
            except Exception as e:
                logger.error("error_processing_file", path=str(file_path), error=str(e))
                continue
    
    def _create_file_object(self, file_path: Path) -> FileObject:
        """Create a FileObject from a file path."""
        stat = file_path.stat()
        
        extension = file_path.suffix.lstrip(".").lower()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        category = get_file_category(extension)
        
        # Get timestamps
        try:
            created_at = datetime.fromtimestamp(stat.st_birthtime)
        except AttributeError:
            # st_birthtime not available on all platforms
            created_at = datetime.fromtimestamp(stat.st_ctime)
        
        modified_at = datetime.fromtimestamp(stat.st_mtime)
        accessed_at = datetime.fromtimestamp(stat.st_atime)
        is_symlink = file_path.is_symlink()
        
        return FileObject(
            id=str(uuid4()),
            folder_id=self.folder_id,
            path=str(file_path),
            filename=file_path.name,
            extension=extension,
            mime_type=mime_type or "",
            size_bytes=stat.st_size,
            created_at=created_at,
            modified_at=modified_at,
            accessed_at=accessed_at,
            is_symlink=is_symlink,
            category=category,
            scanned_at=datetime.now(),
        )
    
    def scan_to_list(
        self,
        root_path: str | Path,
        recursive: bool = True
    ) -> List[FileObject]:
        """
        Scan a directory and return a list of FileObjects.
        
        Args:
            root_path: Root directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of FileObject instances
        """
        return list(self.scan_directory(root_path, recursive))
