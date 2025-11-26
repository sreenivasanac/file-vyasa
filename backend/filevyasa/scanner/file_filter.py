"""File filtering with ignore patterns."""

import fnmatch
from pathlib import Path
from typing import List


class FileFilter:
    """Filter files based on ignore patterns."""

    def __init__(self, ignore_patterns: List[str] | None = None):
        """
        Initialize file filter.

        Args:
            ignore_patterns: List of glob patterns to ignore (e.g., "*.pyc", ".git")
        """
        self.ignore_patterns = ignore_patterns or []

    def should_ignore(self, path: Path) -> bool:
        """
        Check if a path should be ignored based on patterns.

        Args:
            path: Path to check

        Returns:
            True if the path matches any ignore pattern
        """
        name = path.name
        path_str = str(path)

        for pattern in self.ignore_patterns:
            # Check against filename
            if fnmatch.fnmatch(name, pattern):
                return True
            # Check against full path for patterns with /
            if "/" in pattern and fnmatch.fnmatch(path_str, f"*{pattern}*"):
                return True

        return False

    def add_pattern(self, pattern: str) -> None:
        """Add an ignore pattern."""
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)

    def remove_pattern(self, pattern: str) -> None:
        """Remove an ignore pattern."""
        if pattern in self.ignore_patterns:
            self.ignore_patterns.remove(pattern)
