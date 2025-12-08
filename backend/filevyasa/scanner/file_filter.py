"""File filtering with ignore patterns and directory pruning."""

import fnmatch
from pathlib import Path
from typing import List, Optional, Set


class FileFilter:
    """Filter files and directories based on patterns.
    
    Supports three types of filtering:
    1. File patterns - glob patterns matched against filenames (e.g., "*.pyc", ".DS_Store")
    2. Folder names - folder names to skip entirely (e.g., "node_modules", ".git")
    3. Excluded paths - specific paths to exclude (relative to scan root)
    """

    def __init__(
        self,
        file_patterns: Optional[List[str]] = None,
        folder_names: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None,
    ):
        """
        Initialize file filter.

        Args:
            file_patterns: Glob patterns for files to skip (e.g., "*.pyc", ".DS_Store")
            folder_names: Folder names to skip entirely (e.g., "node_modules", ".git")
            excluded_paths: Specific paths to exclude (relative to scan root)
        """
        self.file_patterns = file_patterns or []
        self.folder_names: Set[str] = set(folder_names or [])
        self.excluded_paths: Set[str] = set(excluded_paths or [])

    def should_skip_directory(self, dir_path: Path, root: Path) -> bool:
        """
        Check if a directory should be skipped (not traversed).

        Args:
            dir_path: Full path to the directory
            root: Root path of the scan (for relative path calculation)

        Returns:
            True if the directory should be skipped entirely
        """
        # Check folder name
        if dir_path.name in self.folder_names:
            return True
        
        # Check user-excluded paths (relative to root)
        if self.excluded_paths:
            try:
                rel_path = str(dir_path.relative_to(root))
                # Check exact match and with trailing slash
                if rel_path in self.excluded_paths or f"{rel_path}/" in self.excluded_paths:
                    return True
                # Also check if any excluded path starts with this directory
                for excluded in self.excluded_paths:
                    excluded_clean = excluded.rstrip("/")
                    if rel_path == excluded_clean:
                        return True
            except ValueError:
                pass
        
        return False

    def should_skip_file(self, file_path: Path) -> bool:
        """
        Check if a file should be skipped.

        Args:
            file_path: Path to the file

        Returns:
            True if the file matches any ignore pattern
        """
        name = file_path.name

        for pattern in self.file_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True

        return False

    # Legacy method for backward compatibility
    def should_ignore(self, path: Path) -> bool:
        """Legacy method - checks if path should be ignored (files only)."""
        return self.should_skip_file(path)

    def add_file_pattern(self, pattern: str) -> None:
        """Add a file ignore pattern."""
        if pattern not in self.file_patterns:
            self.file_patterns.append(pattern)

    def remove_file_pattern(self, pattern: str) -> None:
        """Remove a file ignore pattern."""
        if pattern in self.file_patterns:
            self.file_patterns.remove(pattern)

    def add_folder_name(self, name: str) -> None:
        """Add a folder name to skip."""
        self.folder_names.add(name)

    def remove_folder_name(self, name: str) -> None:
        """Remove a folder name from skip list."""
        self.folder_names.discard(name)
