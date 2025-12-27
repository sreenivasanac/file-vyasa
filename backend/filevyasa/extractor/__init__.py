"""Extractor module for content extraction from files."""

# ruff: noqa: E402

import warnings

# TODO: Remove when pdfplumber/python-doctr support pypdfium2 5.x (4.30.1 yanked).
# 5.x has breaking changes.
warnings.filterwarnings("ignore", message=".*_tree_closed.*")

from filevyasa.extractor.base import BaseExtractor, MarkItDownMixin
from filevyasa.extractor.factory import enrich_file_object, extract_content, get_extractor
from filevyasa.extractor.google_workspace_extractor import GoogleDocsExtractor
from filevyasa.extractor.image_extractor import ImageExtractor
from filevyasa.extractor.media_extractor import MediaExtractor, MediaTranscriber
from filevyasa.extractor.non_content_extractor import (
    ArchiveExtractor,
    CodeExtractor,
    NoExtensionExtractor,
    NonContentExtractor,
    UnhandledExtractor,
)
from filevyasa.extractor.notebook_extractor import NotebookExtractor
from filevyasa.extractor.office_extractor import OfficeExtractor
from filevyasa.extractor.pdf_extractor import PDFExtractor
from filevyasa.extractor.text_extractor import TextExtractor
from filevyasa.extractor.web_content_extractor import WebContentExtractor

__all__ = [
    "BaseExtractor",
    "MarkItDownMixin",
    "TextExtractor",
    "PDFExtractor",
    "OfficeExtractor",
    "NotebookExtractor",
    "WebContentExtractor",
    "ImageExtractor",
    "MediaExtractor",
    "MediaTranscriber",
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
