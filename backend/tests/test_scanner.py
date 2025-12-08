"""Tests for the scanner module."""

from pathlib import Path

import pytest

from filevyasa.models.enums import FileCategory
from filevyasa.scanner import FileFilter, Scanner


class TestFileFilter:
    """Tests for FileFilter."""

    def test_should_skip_file_exact_match(self):
        """Test skipping files by exact filename pattern."""
        f = FileFilter(file_patterns=[".DS_Store", "*.pyc"])
        assert f.should_skip_file(Path("/some/path/.DS_Store"))
        assert f.should_skip_file(Path("/some/path/test.pyc"))
        assert not f.should_skip_file(Path("/some/path/test.py"))

    def test_should_skip_directory_by_name(self):
        """Test skipping directories by name."""
        root = Path("/project")
        f = FileFilter(folder_names=["__pycache__", "node_modules"])
        assert f.should_skip_directory(root / "__pycache__", root)
        assert f.should_skip_directory(root / "node_modules", root)
        assert not f.should_skip_directory(root / "src", root)

    def test_should_skip_directory_by_excluded_path(self):
        """Test skipping directories by user-excluded path."""
        root = Path("/project")
        f = FileFilter(excluded_paths=["vendor", "build/output"])
        assert f.should_skip_directory(root / "vendor", root)
        assert f.should_skip_directory(root / "build/output", root)
        assert not f.should_skip_directory(root / "src", root)

    def test_add_remove_file_pattern(self):
        """Test adding and removing file patterns."""
        f = FileFilter()
        f.add_file_pattern("*.log")
        assert f.should_skip_file(Path("test.log"))

        f.remove_file_pattern("*.log")
        assert not f.should_skip_file(Path("test.log"))

    def test_add_remove_folder_name(self):
        """Test adding and removing folder names."""
        root = Path("/project")
        f = FileFilter()
        f.add_folder_name("temp")
        assert f.should_skip_directory(root / "temp", root)

        f.remove_folder_name("temp")
        assert not f.should_skip_directory(root / "temp", root)

    def test_legacy_should_ignore(self):
        """Test backward-compatible should_ignore method."""
        f = FileFilter(file_patterns=[".DS_Store", "*.pyc"])
        assert f.should_ignore(Path("/some/path/.DS_Store"))
        assert f.should_ignore(Path("/some/path/test.pyc"))
        assert not f.should_ignore(Path("/some/path/test.py"))


class TestScanner:
    """Tests for Scanner."""

    def test_scan_directory(self, test_files):
        """Test scanning a directory."""
        scanner = Scanner()
        files, skipped = scanner.scan_to_list(test_files)

        assert len(files) >= 2  # At least test.txt and readme.md
        filenames = [f.filename for f in files]
        assert "test.txt" in filenames
        assert "readme.md" in filenames

    def test_scan_with_file_patterns(self, test_files):
        """Test scanning with file patterns to skip."""
        scanner = Scanner(file_patterns=["*.txt"])
        files, skipped = scanner.scan_to_list(test_files)

        for f in files:
            assert f.extension != "txt"
        assert skipped > 0  # Should have skipped .txt files

    def test_file_category_detection(self, test_files):
        """Test that file categories are detected correctly."""
        scanner = Scanner()
        files, _ = scanner.scan_to_list(test_files)

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
        files_recursive, _ = scanner.scan_to_list(test_files, recursive=True)

        # Non-recursive scan
        files_flat, _ = scanner.scan_to_list(test_files, recursive=False)

        # Recursive should find nested.txt
        recursive_names = [f.filename for f in files_recursive]
        flat_names = [f.filename for f in files_flat]

        assert "nested.txt" in recursive_names
        assert "nested.txt" not in flat_names
    
    def test_skipped_count_for_system_files(self, tmp_path):
        """Test that system files are counted as skipped."""
        # Create a .DS_Store file
        ds_store = tmp_path / ".DS_Store"
        ds_store.write_text("fake DS_Store")
        
        # Create a regular file
        regular = tmp_path / "regular.txt"
        regular.write_text("regular content")
        
        scanner = Scanner()
        files, skipped = scanner.scan_to_list(tmp_path)
        
        assert len(files) == 1
        assert files[0].filename == "regular.txt"
        assert skipped == 1  # .DS_Store should be skipped

    def test_directory_pruning(self, tmp_path):
        """Test that ignored directories are not traversed into."""
        # Create node_modules with nested files
        nm = tmp_path / "node_modules" / "pkg" / "deep"
        nm.mkdir(parents=True)
        (nm / "file.js").write_text("content")
        
        # Create __pycache__ with files
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").write_text("bytecode")
        
        # Create regular file
        (tmp_path / "app.js").write_text("content")
        
        scanner = Scanner()
        files, skipped = scanner.scan_to_list(tmp_path)
        
        # Should only find app.js
        assert len(files) == 1
        assert files[0].filename == "app.js"
        # Files inside pruned directories are NOT counted as skipped
        # because we never traverse into them

    def test_excluded_paths(self, tmp_path):
        """Test that user-specified excluded paths are skipped."""
        # Create vendor directory with files
        vendor = tmp_path / "vendor" / "lib"
        vendor.mkdir(parents=True)
        (vendor / "external.js").write_text("content")
        
        # Create build directory
        build = tmp_path / "build"
        build.mkdir()
        (build / "output.js").write_text("content")
        
        # Create regular file
        (tmp_path / "app.js").write_text("content")
        
        scanner = Scanner(excluded_paths=["vendor", "build"])
        files, skipped = scanner.scan_to_list(tmp_path)
        
        # Should only find app.js
        assert len(files) == 1
        assert files[0].filename == "app.js"
