"""Web content extractor for HTML and XML files."""

from pathlib import Path
from typing import Any, Dict, Tuple

import structlog

from filevyasa.extractor.base import BaseExtractor, MarkItDownMixin

logger = structlog.get_logger()


class WebContentExtractor(MarkItDownMixin, BaseExtractor):
    """Extractor for HTML and XML files."""

    @classmethod
    def supported_extensions(cls) -> list[str]:
        return ["html", "htm", "xml"]

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract content from HTML/XML files."""
        metadata = {}
        ext = file_path.suffix.lower()

        # Try markitdown first (converts HTML to markdown nicely)
        md = self._get_markitdown()
        if md is not None:
            try:
                result = md.convert(str(file_path))
                content = result.text_content if result.text_content else ""

                if content.strip():
                    metadata["extraction_method"] = "markitdown"
                    metadata["source_type"] = ext
                    return content, metadata

            except Exception as e:
                logger.error("markitdown_extraction_failed", path=str(file_path), error=str(e))

        # Fallback: read as text
        return self._fallback_extract(file_path, metadata)

    def _fallback_extract(self, file_path: Path, metadata: Dict) -> Tuple[str, Dict[str, Any]]:
        """Fallback extraction by reading file as text."""
        try:
            content = file_path.read_text(encoding="utf-8")
            metadata["extraction_method"] = "text_read"
            metadata["source_type"] = file_path.suffix.lower()
            return content, metadata
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding="latin-1")
                metadata["extraction_method"] = "text_read"
                metadata["encoding"] = "latin-1"
                return content, metadata
            except Exception as e:
                logger.warning("web_content_fallback_failed", path=str(file_path), error=str(e))

        return "[Unable to extract content from file]", {"extraction_method": "fallback"}
