"""EPUB ebook extractor using markitdown."""

from pathlib import Path
from typing import Any, Dict, Tuple

import structlog

from filevyasa.extractor.base import BaseExtractor, MarkItDownMixin

logger = structlog.get_logger()

MIN_TEXT_LENGTH = 10


class EpubExtractor(MarkItDownMixin, BaseExtractor):
    """Extractor for EPUB ebook files using markitdown."""

    @classmethod
    def supported_extensions(cls) -> list[str]:
        return ["epub"]

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract content from EPUB files."""
        metadata = {}

        md = self._get_markitdown()
        if md is not None:
            try:
                result = md.convert(str(file_path))
                content = result.text_content if result.text_content else ""

                if len(content.strip()) >= MIN_TEXT_LENGTH:
                    metadata["extraction_method"] = "markitdown"
                    metadata["source_type"] = "epub"
                    return content, metadata

                logger.info(
                    "markitdown_insufficient_content",
                    path=str(file_path),
                    text_length=len(content.strip()),
                )
            except Exception as e:
                logger.error("epub_extraction_failed", path=str(file_path), error=str(e))

        return "[Unable to extract content from EPUB file]", {
            "extraction_method": "failed",
            "error": "markitdown_unavailable_or_failed"
        }
