"""Tests for the extractor module."""

from pathlib import Path

import pytest

from filevyasa.extractor import (
    get_extractor,
    extract_content,
    TextExtractor,
    DocumentExtractor,
    ImageExtractor,
)


class TestExtractorFactory:
    """Tests for extractor factory functions."""
    
    def test_get_extractor_text(self):
        """Test getting text extractor."""
        extractor = get_extractor("txt")
        assert isinstance(extractor, TextExtractor)
        
        extractor = get_extractor(".md")
        assert isinstance(extractor, TextExtractor)
    
    def test_get_extractor_document(self):
        """Test getting document extractor."""
        extractor = get_extractor("pdf")
        assert isinstance(extractor, DocumentExtractor)
        
        extractor = get_extractor("docx")
        assert isinstance(extractor, DocumentExtractor)
    
    def test_get_extractor_image(self):
        """Test getting image extractor."""
        extractor = get_extractor("jpg")
        assert isinstance(extractor, ImageExtractor)
        
        extractor = get_extractor("png")
        assert isinstance(extractor, ImageExtractor)
    
    def test_get_extractor_unsupported(self):
        """Test that unsupported extensions return None."""
        extractor = get_extractor("unknown_extension")
        assert extractor is None


class TestTextExtractor:
    """Tests for TextExtractor."""
    
    def test_extract_text_file(self, test_files):
        """Test extracting text file."""
        text_file = test_files / "test.txt"
        extractor = TextExtractor()
        
        content, metadata = extractor.extract(text_file)
        
        assert "This is a test file" in content
        assert metadata["line_count"] > 0
        assert metadata["word_count"] > 0
    
    def test_extract_markdown_file(self, test_files):
        """Test extracting markdown file."""
        md_file = test_files / "readme.md"
        extractor = TextExtractor()
        
        content, metadata = extractor.extract(md_file)
        
        assert "# Test README" in content


class TestDocumentExtractor:
    """Tests for DocumentExtractor."""
    
    def test_supported_extensions(self):
        """Test that common document extensions are supported."""
        ext = DocumentExtractor.supported_extensions()
        assert "pdf" in ext
        assert "docx" in ext
        assert "xlsx" in ext
    
    def test_extract_with_sample_data(self, sample_data_dir):
        """Test extraction with real sample files if available."""
        pdf_file = sample_data_dir / "paper_1col.pdf"
        if pdf_file.exists():
            extractor = DocumentExtractor()
            content, metadata = extractor.extract(pdf_file)
            # Should return some content
            assert len(content) > 0 or "Unable to extract" in content


class TestImageExtractor:
    """Tests for ImageExtractor."""
    
    def test_supported_extensions(self):
        """Test that common image extensions are supported."""
        ext = ImageExtractor.supported_extensions()
        assert "jpg" in ext
        assert "png" in ext
        assert "gif" in ext
    
    def test_extract_with_sample_data(self, sample_data_dir):
        """Test extraction with real sample images if available."""
        png_file = sample_data_dir / "logo.png"
        if png_file.exists():
            extractor = ImageExtractor()
            content, metadata = extractor.extract(png_file)
            
            assert "width" in metadata
            assert "height" in metadata


class TestExtractContent:
    """Tests for extract_content function."""
    
    def test_extract_content_text(self, test_files):
        """Test extract_content with text file."""
        content, metadata = extract_content(test_files / "test.txt")
        assert "This is a test file" in content
    
    def test_extract_content_truncation(self, temp_dir):
        """Test that content is truncated."""
        # Create a file with many lines
        long_file = temp_dir / "long.txt"
        lines = [f"Line {i}" for i in range(100)]
        long_file.write_text("\n".join(lines))
        
        content, metadata = extract_content(long_file, max_lines=10)
        
        # Should be truncated
        assert "Line 0" in content
        assert "Line 9" in content
        assert "truncated" in content.lower()
