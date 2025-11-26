"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def sample_data_dir():
    """Return path to sample_data directory."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "sample_data"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_files(temp_dir):
    """Create test files in temporary directory."""
    # Create text file
    text_file = temp_dir / "test.txt"
    text_file.write_text("This is a test file.\nWith multiple lines.\n")

    # Create markdown file
    md_file = temp_dir / "readme.md"
    md_file.write_text("# Test README\n\nThis is a test markdown file.\n")

    # Create subdirectory with files
    sub_dir = temp_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "nested.txt").write_text("Nested file content")

    return temp_dir
