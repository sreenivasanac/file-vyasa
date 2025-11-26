"""Extractor module for content extraction from files."""

from filevyasa.extractor.base import BaseExtractor
from filevyasa.extractor.document_extractor import DocumentExtractor
from filevyasa.extractor.factory import enrich_file_object, extract_content, get_extractor
from filevyasa.extractor.image_extractor import ImageExtractor
from filevyasa.extractor.non_content_extractor import (
    ArchiveExtractor,
    CodeExtractor,
    GoogleDocsExtractor,
    NoExtensionExtractor,
    NonContentExtractor,
    UnhandledExtractor,
)
from filevyasa.extractor.text_extractor import TextExtractor

__all__ = [
    "BaseExtractor",
    "TextExtractor",
    "DocumentExtractor",
    "ImageExtractor",
    "NonContentExtractor",
    "CodeExtractor",
    "ArchiveExtractor",
    "GoogleDocsExtractor",
    "UnhandledExtractor",
    "NoExtensionExtractor",
    "get_extractor",
    "extract_content",
    "enrich_file_object",
]
