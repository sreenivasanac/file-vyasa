"""Base extractor interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Tuple


class BaseExtractor(ABC):
    """Base class for content extractors."""
    
    @abstractmethod
    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Extract content and metadata from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (content_markdown, metadata_dict)
        """
        pass
    
    @classmethod
    @abstractmethod
    def supported_extensions(cls) -> list[str]:
        """Return list of supported file extensions (without dot)."""
        pass
    
    def truncate_content(self, content: str, max_lines: int = 50) -> str:
        """Truncate content to max_lines."""
        lines = content.split("\n")
        if len(lines) > max_lines:
            return "\n".join(lines[:max_lines]) + "\n...[truncated]"
        return content
