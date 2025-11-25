"""Document extractor using markitdown for Office docs, PDFs, etc."""

from pathlib import Path
from typing import Any, Dict, Tuple

import structlog

from filevyasa.extractor.base import BaseExtractor

logger = structlog.get_logger()


class DocumentExtractor(BaseExtractor):
    """Extractor for documents using markitdown library."""
    
    def __init__(self):
        self._markitdown = None
    
    def _get_markitdown(self):
        """Lazy load markitdown to avoid import errors if not installed."""
        if self._markitdown is None:
            try:
                from markitdown import MarkItDown
                self._markitdown = MarkItDown()
            except ImportError:
                logger.warning("markitdown_not_installed")
                return None
        return self._markitdown
    
    @classmethod
    def supported_extensions(cls) -> list[str]:
        return [
            "pdf",
            "docx", "doc",
            "xlsx", "xls", "csv",
            "pptx", "ppt",
            "rtf",
            "odt", "ods", "odp",
            "html", "htm",
            "xml",
            "json",
            "ipynb",
        ]
    
    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract content from documents using markitdown."""
        metadata = {}
        
        md = self._get_markitdown()
        if md is None:
            return self._fallback_extract(file_path, metadata)
        
        try:
            result = md.convert(str(file_path))
            content = result.text_content if result.text_content else ""
            
            # Add basic metadata
            metadata["extraction_method"] = "markitdown"
            metadata["source_type"] = file_path.suffix.lower()
            
            return content, metadata
            
        except Exception as e:
            logger.error("markitdown_extraction_failed", path=str(file_path), error=str(e))
            return self._fallback_extract(file_path, metadata)
    
    def _fallback_extract(self, file_path: Path, metadata: Dict) -> Tuple[str, Dict[str, Any]]:
        """Fallback extraction for when markitdown fails."""
        metadata["extraction_method"] = "fallback"
        ext = file_path.suffix.lower()
        
        # Try to read as text for certain formats
        if ext in [".csv", ".html", ".htm", ".xml", ".json"]:
            try:
                content = file_path.read_text(encoding="utf-8")
                return content, metadata
            except Exception:
                pass
        
        # For PDFs, try pdfplumber
        if ext == ".pdf":
            try:
                import pdfplumber
                with pdfplumber.open(str(file_path)) as pdf:
                    pages = []
                    for page in pdf.pages[:10]:  # Limit to first 10 pages
                        text = page.extract_text()
                        if text:
                            pages.append(text)
                    content = "\n\n---\n\n".join(pages)
                    metadata["page_count"] = len(pdf.pages)
                    metadata["extraction_method"] = "pdfplumber"
                    return content, metadata
            except Exception as e:
                logger.warning("pdfplumber_failed", error=str(e))
        
        # For DOCX, try python-docx
        if ext == ".docx":
            try:
                from docx import Document
                doc = Document(str(file_path))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                content = "\n\n".join(paragraphs)
                metadata["paragraph_count"] = len(paragraphs)
                metadata["extraction_method"] = "python-docx"
                return content, metadata
            except Exception as e:
                logger.warning("python_docx_failed", error=str(e))
        
        return f"[Unable to extract content from {ext} file]", metadata
