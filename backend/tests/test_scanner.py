"""Tests for the scanner module."""

from pathlib import Path

import pytest

from filevyasa.models.enums import FileCategory
from filevyasa.scanner import FileFilter, Scanner


class TestFileFilter:
    """Tests for FileFilter."""

    def test_should_ignore_exact_match(self):
        """Test ignoring by exact filename."""
        f = FileFilter([".DS_Store", "*.pyc"])
        assert f.should_ignore(Path("/some/path/.DS_Store"))
        assert f.should_ignore(Path("/some/path/test.pyc"))
        assert not f.should_ignore(Path("/some/path/test.py"))

    def test_should_ignore_directory_pattern(self):
        """Test ignoring directory patterns."""
        f = FileFilter(["__pycache__", "node_modules"])
        assert f.should_ignore(Path("/some/__pycache__"))
        assert f.should_ignore(Path("/project/node_modules"))

    def test_add_remove_pattern(self):
        """Test adding and removing patterns."""
        f = FileFilter([])
        f.add_pattern("*.log")
        assert f.should_ignore(Path("test.log"))

        f.remove_pattern("*.log")
        assert not f.should_ignore(Path("test.log"))


class TestScanner:
    """Tests for Scanner."""

    def test_scan_directory(self, test_files):
        """Test scanning a directory."""
        scanner = Scanner()
        files = scanner.scan_to_list(test_files)

        assert len(files) >= 2  # At least test.txt and readme.md
        filenames = [f.filename for f in files]
        assert "test.txt" in filenames
        assert "readme.md" in filenames

    def test_scan_with_ignore_patterns(self, test_files):
        """Test scanning with ignore patterns."""
        scanner = Scanner(ignore_patterns=["*.txt"])
        files = scanner.scan_to_list(test_files)

        for f in files:
            assert f.extension != "txt"

    def test_file_category_detection(self, test_files):
        """Test that file categories are detected correctly."""
        scanner = Scanner()
        files = scanner.scan_to_list(test_files)

        for f in files:
            if f.extension == "txt":
                assert f.category == FileCategory.TEXT
            elif f.extension == "md":
                assert f.category == FileCategory.TEXT

    def test_scan_nonexistent_directory(self):
        """Test scanning a non-existent directory raises error."""
        scanner = Scanner()
        with pytest.raises(ValueError, match="does not exist"):
            scanner.scan_to_list("/nonexistent/path")

    def test_scan_recursive(self, test_files):
        """Test recursive scanning."""
        scanner = Scanner()

        # Recursive scan
        files_recursive = scanner.scan_to_list(test_files, recursive=True)

        # Non-recursive scan
        files_flat = scanner.scan_to_list(test_files, recursive=False)

        # Recursive should find nested.txt
        recursive_names = [f.filename for f in files_recursive]
        flat_names = [f.filename for f in files_flat]

        assert "nested.txt" in recursive_names
        assert "nested.txt" not in flat_names
