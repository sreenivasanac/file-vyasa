"""Text file extractor for plain text and markdown files."""

from pathlib import Path
from typing import Any, Dict, Tuple

from filevyasa.extractor.base import BaseExtractor


class TextExtractor(BaseExtractor):
    """Extractor for plain text and markdown files."""

    @classmethod
    def supported_extensions(cls) -> list[str]:
        return ["txt", "md", "markdown", "rst", "log", "ini", "cfg", "conf"]

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract content from text files."""
        metadata = {}

        try:
            # Try UTF-8 first, then fall back to latin-1
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="latin-1")

            # Count lines and words for metadata
            lines = content.split("\n")
            words = content.split()
            metadata["line_count"] = len(lines)
            metadata["word_count"] = len(words)
            metadata["encoding"] = "utf-8"

            return content, metadata

        except Exception as e:
            return f"[Error reading file: {str(e)}]", {"error": str(e)}
