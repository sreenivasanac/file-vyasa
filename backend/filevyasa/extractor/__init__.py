"""Extractor module for content extraction from files."""

from filevyasa.extractor.base import BaseExtractor
from filevyasa.extractor.text_extractor import TextExtractor
from filevyasa.extractor.document_extractor import DocumentExtractor
from filevyasa.extractor.image_extractor import ImageExtractor
from filevyasa.extractor.factory import get_extractor, extract_content, enrich_file_object

__all__ = [
    "BaseExtractor",
    "TextExtractor",
    "DocumentExtractor",
    "ImageExtractor",
    "get_extractor",
    "extract_content",
    "enrich_file_object",
]
