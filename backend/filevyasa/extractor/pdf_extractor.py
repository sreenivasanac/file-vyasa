"""PDF extractor using pdfplumber with OCR fallback for image-based PDFs."""

from pathlib import Path
from typing import Any, Dict, Tuple

import structlog

from filevyasa.extractor.base import BaseExtractor, MarkItDownMixin

logger = structlog.get_logger()

# Minimum text length to consider extraction successful (avoid OCR for text-rich PDFs)
MIN_TEXT_LENGTH_FOR_OCR_SKIP = 100
# Max pages to OCR for image-based PDFs (speed optimization)
MAX_OCR_PAGES = 2


class PDFExtractor(MarkItDownMixin, BaseExtractor):
    """Extractor for PDF files using markitdown, pdfplumber, and OCR fallback."""

    @classmethod
    def supported_extensions(cls) -> list[str]:
        return ["pdf"]

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract content from PDF files."""
        metadata = {}

        # Try markitdown first
        md = self._get_markitdown()
        if md is not None:
            try:
                result = md.convert(str(file_path))
                content = result.text_content if result.text_content else ""

                if len(content.strip()) >= MIN_TEXT_LENGTH_FOR_OCR_SKIP:
                    metadata["extraction_method"] = "markitdown"
                    metadata["source_type"] = ".pdf"
                    return content, metadata

                logger.info(
                    "markitdown_insufficient_content",
                    path=str(file_path),
                    text_length=len(content.strip()),
                )
            except Exception as e:
                logger.error("markitdown_extraction_failed", path=str(file_path), error=str(e))

        # Fall back to pdfplumber + OCR
        return self._extract_pdf_with_fallback(file_path, metadata)

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
                for page in pdf.pages[:4]:
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

        metadata["extraction_method"] = "fallback"
        return "[Unable to extract content from PDF file]", metadata

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
