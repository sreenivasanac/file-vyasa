"""Factory for selecting appropriate extractor based on file type."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from filevyasa.config import settings
from filevyasa.extractor.base import BaseExtractor
from filevyasa.extractor.text_extractor import TextExtractor
from filevyasa.extractor.document_extractor import DocumentExtractor
from filevyasa.extractor.image_extractor import ImageExtractor
from filevyasa.models.file_object import FileObject


# Instantiate extractors
_extractors: list[BaseExtractor] = [
    TextExtractor(),
    DocumentExtractor(),
    ImageExtractor(),
]

# Build extension to extractor map
_extension_map: Dict[str, BaseExtractor] = {}
for extractor in _extractors:
    for ext in extractor.supported_extensions():
        _extension_map[ext.lower()] = extractor


def get_extractor(extension: str) -> Optional[BaseExtractor]:
    """
    Get the appropriate extractor for a file extension.
    
    Args:
        extension: File extension (with or without dot)
        
    Returns:
        Extractor instance or None if not supported
    """
    ext = extension.lower().lstrip(".")
    return _extension_map.get(ext)


def extract_content(
    file_path: str | Path,
    max_lines: int | None = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Extract content from a file.
    
    Args:
        file_path: Path to the file
        max_lines: Maximum lines to return (default from settings)
        
    Returns:
        Tuple of (content_preview, metadata)
    """
    path = Path(file_path)
    extension = path.suffix.lstrip(".")
    
    extractor = get_extractor(extension)
    if extractor is None:
        return "[Unsupported file type]", {"supported": False}
    
    content, metadata = extractor.extract(path)
    
    # Truncate content
    max_lines = max_lines or settings.max_content_lines
    content = extractor.truncate_content(content, max_lines)
    
    return content, metadata


def enrich_file_object(file_obj: FileObject, max_lines: int | None = None) -> FileObject:
    """
    Enrich a FileObject with extracted content and metadata.
    
    Args:
        file_obj: FileObject to enrich
        max_lines: Maximum lines for content preview
        
    Returns:
        Enriched FileObject
    """
    content, metadata = extract_content(file_obj.path, max_lines)
    
    file_obj.content_preview = content
    
    # Merge metadata
    if "exif" in metadata:
        file_obj.exif_data = metadata.pop("exif")
    file_obj.metadata.update(metadata)
    
    return file_obj
