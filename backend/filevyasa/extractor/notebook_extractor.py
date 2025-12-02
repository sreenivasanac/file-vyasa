"""Jupyter notebook extractor for .ipynb files."""

from pathlib import Path
from typing import Any, Dict, Tuple

import structlog

from filevyasa.extractor.base import BaseExtractor, MarkItDownMixin

logger = structlog.get_logger()


class NotebookExtractor(MarkItDownMixin, BaseExtractor):
    """Extractor for Jupyter notebook files."""

    @classmethod
    def supported_extensions(cls) -> list[str]:
        return ["ipynb"]

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract content from Jupyter notebooks."""
        metadata = {}

        # Try markitdown first (handles notebook structure well)
        md = self._get_markitdown()
        if md is not None:
            try:
                result = md.convert(str(file_path))
                content = result.text_content if result.text_content else ""

                if content.strip():
                    metadata["extraction_method"] = "markitdown"
                    metadata["source_type"] = ".ipynb"
                    return content, metadata

            except Exception as e:
                logger.error("markitdown_extraction_failed", path=str(file_path), error=str(e))

        # Fallback: parse notebook JSON directly
        return self._fallback_extract(file_path, metadata)

    def _fallback_extract(self, file_path: Path, metadata: Dict) -> Tuple[str, Dict[str, Any]]:
        """Fallback extraction by parsing notebook JSON."""
        import json

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                notebook = json.load(f)

            cells = notebook.get("cells", [])
            content_parts = []
            code_cells = 0
            markdown_cells = 0

            for cell in cells:
                cell_type = cell.get("cell_type", "")
                source = cell.get("source", [])

                # Source can be a list of lines or a single string
                if isinstance(source, list):
                    cell_content = "".join(source)
                else:
                    cell_content = source

                if cell_type == "markdown":
                    markdown_cells += 1
                    content_parts.append(cell_content)
                elif cell_type == "code":
                    code_cells += 1
                    content_parts.append(f"```python\n{cell_content}\n```")

            metadata["extraction_method"] = "json_parse"
            metadata["code_cells"] = code_cells
            metadata["markdown_cells"] = markdown_cells
            metadata["total_cells"] = len(cells)

            content = "\n\n".join(content_parts)
            return content, metadata

        except Exception as e:
            logger.warning("notebook_fallback_failed", path=str(file_path), error=str(e))
            return "[Unable to extract content from notebook]", {"extraction_method": "fallback"}
