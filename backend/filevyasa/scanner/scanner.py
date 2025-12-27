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
    "gdoc": FileCategory.DOCUMENT,  # Google Docs
    "gform": FileCategory.DOCUMENT,  # Google Forms

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
    "gsheet": FileCategory.SPREADSHEET,  # Google Sheets

    # Presentations
    "pptx": FileCategory.PRESENTATION,
    "ppt": FileCategory.PRESENTATION,
    "key": FileCategory.PRESENTATION,
    "odp": FileCategory.PRESENTATION,
    "gslides": FileCategory.PRESENTATION,  # Google Slides

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
    "gdraw": FileCategory.IMAGE,  # Google Drawings

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
    """Directory scanner for discovering and cataloging files.

    Uses os.walk() with directory pruning to efficiently skip ignored folders
    like node_modules, .git, etc. without traversing into them.
    """

    def __init__(
        self,
        file_patterns: Optional[List[str]] = None,
        folder_names: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None,
        folder_id: Optional[str] = None,
    ):
        """
        Initialize the scanner.

        Args:
            file_patterns: Glob patterns for files to skip (defaults to config)
            folder_names: Folder names to skip entirely (defaults to config)
            excluded_paths: Specific paths to exclude (relative to scan root)
            folder_id: Optional folder ID for associating scanned files
        """
        self.file_filter = FileFilter(
            file_patterns=file_patterns or list(settings.ignore_file_patterns),
            folder_names=folder_names or list(settings.ignore_folder_names),
            excluded_paths=excluded_paths or [],
        )
        self.folder_id = folder_id or str(uuid4())
        self._skipped_files = 0
        self._skipped_dirs = 0

    def scan_directory(
        self,
        root_path: str | Path,
        recursive: bool = True
    ) -> Generator[FileObject, None, None]:
        """
        Scan a directory and yield FileObject instances.

        Uses os.walk() with topdown=True to prune directories before traversal,
        avoiding iteration through ignored folders like node_modules.

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
            # Use os.walk with topdown=True for efficient directory pruning
            for dirpath, dirnames, filenames in os.walk(root, topdown=True):
                current_dir = Path(dirpath)

                # PRUNE directories in-place to prevent traversal into ignored folders
                original_count = len(dirnames)
                dirnames[:] = [
                    d for d in dirnames
                    if not self.file_filter.should_skip_directory(current_dir / d, root)
                ]
                self._skipped_dirs += original_count - len(dirnames)

                # Process files in current directory
                for filename in filenames:
                    file_path = current_dir / filename

                    # Skip ignored files
                    if self.file_filter.should_skip_file(file_path):
                        self._skipped_files += 1
                        continue

                    try:
                        file_obj = self._create_file_object(file_path)
                        yield file_obj
                    except Exception as e:
                        logger.error("error_processing_file", path=str(file_path), error=str(e))
                        continue
        else:
            # Non-recursive: just list top-level files
            for item in root.iterdir():
                if item.is_file() and not self.file_filter.should_skip_file(item):
                    try:
                        yield self._create_file_object(item)
                    except Exception as e:
                        logger.error("error_processing_file", path=str(item), error=str(e))
                        continue
                elif item.is_file():
                    self._skipped_files += 1

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
            inode=stat.st_ino,  # Unique file ID - survives rename/move on same filesystem
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
    ) -> tuple[List[FileObject], int]:
        """
        Scan a directory and return a list of FileObjects with skipped count.

        Args:
            root_path: Root directory to scan
            recursive: Whether to scan subdirectories

        Returns:
            Tuple of (List of FileObject instances, count of skipped files)
        """
        self._skipped_files = 0
        self._skipped_dirs = 0
        files = list(self.scan_directory(root_path, recursive))

        if self._skipped_files > 0 or self._skipped_dirs > 0:
            logger.info(
                "scan_complete",
                files_found=len(files),
                skipped_files=self._skipped_files,
                skipped_directories=self._skipped_dirs
            )

        return files, self._skipped_files
