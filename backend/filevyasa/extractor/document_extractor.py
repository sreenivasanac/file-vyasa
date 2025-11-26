"""Document extractor using markitdown for Office docs, PDFs, etc."""

from pathlib import Path
from typing import Any, Dict, Tuple

import structlog

from filevyasa.extractor.base import BaseExtractor

logger = structlog.get_logger()

# Minimum text length to consider extraction successful (avoid OCR for text-rich PDFs)
MIN_TEXT_LENGTH_FOR_OCR_SKIP = 100
# Max pages to OCR for image-based PDFs (speed optimization)
MAX_OCR_PAGES = 2


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

            # If markitdown returns insufficient content, try fallback
            if len(content.strip()) < MIN_TEXT_LENGTH_FOR_OCR_SKIP:
                logger.info(
                    "markitdown_insufficient_content",
                    path=str(file_path),
                    text_length=len(content.strip()),
                )
                return self._fallback_extract(file_path, metadata)

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

        # For PDFs, try pdfplumber first, then OCR if needed
        if ext == ".pdf":
            content, metadata = self._extract_pdf_with_fallback(file_path, metadata)
            if content:
                return content, metadata

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

    def _extract_pdf_with_fallback(
        self, file_path: Path, metadata: Dict
    ) -> Tuple[str, Dict[str, Any]]:
        """Extract PDF content using pdfplumber, falling back to OCR for image-based PDFs."""
        content = ""

        # First try pdfplumber for text-based PDFs
        try:
            import pdfplumber

            with pdfplumber.open(str(file_path)) as pdf:
                pages = []
                for page in pdf.pages[:10]:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                content = "\n\n---\n\n".join(pages)
                metadata["page_count"] = len(pdf.pages)

                # If we got sufficient text, return it
                if len(content.strip()) >= MIN_TEXT_LENGTH_FOR_OCR_SKIP:
                    metadata["extraction_method"] = "pdfplumber"
                    return content, metadata

                logger.info(
                    "pdf_text_extraction_insufficient",
                    path=str(file_path),
                    text_length=len(content.strip()),
                )
        except Exception as e:
            logger.warning("pdfplumber_failed", error=str(e))

        # Fall back to OCR for image-based PDFs (using doctr - pure Python)
        ocr_content, ocr_success = self._ocr_pdf_with_doctr(file_path)
        if ocr_success and ocr_content:
            metadata["extraction_method"] = "doctr_ocr"
            metadata["ocr_pages"] = MAX_OCR_PAGES
            return ocr_content, metadata

        # Return whatever we got from pdfplumber if OCR failed
        if content:
            metadata["extraction_method"] = "pdfplumber"
            return content, metadata

        return "", metadata

    def _ocr_pdf_with_doctr(self, file_path: Path) -> Tuple[str, bool]:
        """OCR PDF pages using doctr (pure Python, no Tesseract dependency).

        Uses speed-optimized settings:
        - fast_base detection model for speed
        - crnn_vgg16_bn recognition (good speed/accuracy balance)
        - assume_straight_pages=True to skip orientation detection
        - Only processes first MAX_OCR_PAGES pages
        """
        try:
            from doctr.io import DocumentFile
            from doctr.models import ocr_predictor

            logger.info("starting_pdf_ocr_doctr", path=str(file_path), max_pages=MAX_OCR_PAGES)

            # Load PDF and limit to first N pages
            doc = DocumentFile.from_pdf(str(file_path))
            doc = doc[:MAX_OCR_PAGES]

            # Speed-optimized OCR predictor
            model = ocr_predictor(
                det_arch="fast_base",
                reco_arch="crnn_vgg16_bn",
                pretrained=True,
                assume_straight_pages=True,  # Skip orientation detection for speed
            )

            result = model(doc)

            # Extract text from result
            text_parts = []
            for page in result.pages:
                page_lines = []
                for block in page.blocks:
                    for line in block.lines:
                        line_text = " ".join([word.value for word in line.words])
                        page_lines.append(line_text)
                if page_lines:
                    text_parts.append("\n".join(page_lines))

            content = "\n\n---\n\n".join(text_parts)
            logger.info(
                "pdf_ocr_complete",
                path=str(file_path),
                pages_processed=len(doc),
                total_text_length=len(content),
            )
            return content, True

        except ImportError as e:
            logger.warning(
                "ocr_dependencies_missing",
                error=str(e),
                hint="Install python-doctr[torch] for OCR support",
            )
            return "", False
        except Exception as e:
            logger.error("pdf_ocr_failed", path=str(file_path), error=str(e))
            return "", False
