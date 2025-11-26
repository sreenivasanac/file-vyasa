"""Extractor for Google Workspace files (.gdoc, .gsheet, .gslides, .gform, .gdraw).

Parses local shortcut files and uses Google APIs to fetch actual content and metadata.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from filevyasa.extractor.base import BaseExtractor

logger = logging.getLogger(__name__)


class GoogleDocsExtractor(BaseExtractor):
    """Extractor for Google Workspace shortcut files.

    Parses local .gdoc/.gsheet/.gslides/.gform/.gdraw files to extract document IDs,
    then uses Google APIs to fetch actual content and metadata.

    Requires Google service account credentials configured via:
    - FILEVYASA_GOOGLE_CREDENTIALS_PATH environment variable, or
    - google.credentials_path in settings.yaml

    Documents must be shared with the service account email for access.
    Falls back to simple description if credentials are not configured.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/documents.readonly",
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/presentations.readonly",
        "https://www.googleapis.com/auth/forms.body.readonly",
    ]

    def __init__(self):
        self._credentials = None
        self._drive_service = None
        self._docs_service = None
        self._sheets_service = None
        self._slides_service = None
        self._forms_service = None
        self._initialized = False
        self._last_credentials_path: str | None = None

    @classmethod
    def supported_extensions(cls) -> List[str]:
        return ["gdoc", "gsheet", "gslides", "gform", "gdraw"]

    def _get_type_label(self, ext: str) -> str:
        labels = {
            "gdoc": "Google Docs",
            "gsheet": "Google Sheets",
            "gslides": "Google Slides",
            "gform": "Google Forms",
            "gdraw": "Google Drawings",
        }
        return labels.get(ext, "Google Docs")

    def _init_services(self) -> bool:
        """Initialize Google API services lazily. Returns True if successful."""
        from filevyasa.config import settings

        current_credentials_path = settings.google_credentials_path

        # Re-initialize if credentials path changed
        if self._initialized and self._last_credentials_path == current_credentials_path:
            return self._credentials is not None

        self._initialized = True
        self._last_credentials_path = current_credentials_path

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
        except ImportError:
            logger.warning(
                "Google API libraries not installed. "
                "Install with: pip install google-api-python-client google-auth"
            )
            return False

        credentials_path = current_credentials_path
        if not credentials_path:
            logger.debug("Google credentials path not configured, skipping API extraction")
            return False

        credentials_file = Path(credentials_path)
        if not credentials_file.exists():
            logger.warning(f"Google credentials file not found: {credentials_path}")
            return False

        try:
            self._credentials = Credentials.from_service_account_file(
                str(credentials_file), scopes=self.SCOPES
            )
            self._drive_service = build("drive", "v3", credentials=self._credentials)
            self._docs_service = build("docs", "v1", credentials=self._credentials)
            self._sheets_service = build("sheets", "v4", credentials=self._credentials)
            self._slides_service = build("slides", "v1", credentials=self._credentials)
            self._forms_service = build("forms", "v1", credentials=self._credentials)
            logger.info("Google API services initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Google API services: {e}")
            return False

    def _parse_shortcut_file(self, file_path: Path) -> Optional[str]:
        """Parse local Google Workspace shortcut file to extract document ID."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            doc_id = data.get("doc_id") or data.get("resourceId") or data.get("resource_id")
            if not doc_id and "url" in data:
                # Extract ID from URL if present
                url = data["url"]
                # URLs like https://docs.google.com/document/d/DOC_ID/edit
                parts = url.split("/d/")
                if len(parts) > 1:
                    doc_id = parts[1].split("/")[0]
            return doc_id
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to parse shortcut file {file_path}: {e}")
            return None

    def extract(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract content from Google Workspace document."""
        ext = file_path.suffix.lower().lstrip(".")
        filename = file_path.name
        type_label = self._get_type_label(ext)

        # Try to parse the shortcut file
        doc_id = self._parse_shortcut_file(file_path)
        if not doc_id:
            return f"{type_label} file with name {filename}", {
                "extraction_method": "skipped",
                "reason": "failed_to_parse_shortcut",
                "file_type": ext,
            }

        # Try to initialize Google API services
        if not self._init_services():
            return f"{type_label} file with name {filename}", {
                "extraction_method": "skipped",
                "reason": "google_credentials_not_configured",
                "file_type": ext,
                "document_id": doc_id,
            }

        # Extract based on file type
        try:
            if ext == "gdoc":
                return self._extract_docs(doc_id, filename)
            elif ext == "gsheet":
                return self._extract_sheets(doc_id, filename)
            elif ext == "gslides":
                return self._extract_slides(doc_id, filename)
            elif ext == "gform":
                return self._extract_forms(doc_id, filename)
            elif ext == "gdraw":
                return self._extract_drawings(doc_id, filename)
            else:
                return self._extract_fallback(doc_id, ext, filename)
        except Exception as e:
            logger.error(f"Failed to extract {ext} content for {filename}: {e}")
            return f"{type_label} file with name {filename}", {
                "extraction_method": "failed",
                "reason": str(e),
                "file_type": ext,
                "document_id": doc_id,
            }

    def _get_drive_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get common metadata from Drive API."""
        try:
            file_metadata = self._drive_service.files().get(
                fileId=file_id,
                fields="name,createdTime,modifiedTime,owners,webViewLink,mimeType"
            ).execute()
            return {
                "title": file_metadata.get("name"),
                "created_time": file_metadata.get("createdTime"),
                "modified_time": file_metadata.get("modifiedTime"),
                "owner": (file_metadata.get("owners", [{}])[0].get("displayName")
                          if file_metadata.get("owners") else None),
                "owner_email": (file_metadata.get("owners", [{}])[0].get("emailAddress")
                                if file_metadata.get("owners") else None),
                "web_view_link": file_metadata.get("webViewLink"),
                "mime_type": file_metadata.get("mimeType"),
            }
        except Exception as e:
            logger.warning(f"Failed to get Drive metadata for {file_id}: {e}")
            return {}

    def _extract_docs(self, doc_id: str, filename: str) -> Tuple[str, Dict[str, Any]]:
        """Extract Google Docs content via Docs API."""
        document = self._docs_service.documents().get(documentId=doc_id).execute()
        drive_meta = self._get_drive_metadata(doc_id)

        # Extract text content
        text_content = self._extract_text_from_document(document)
        title = document.get("title", filename)

        content = f"# {title}\n\n{text_content}"

        metadata = {
            "extraction_method": "google_docs_api",
            "file_type": "gdoc",
            "document_id": doc_id,
            "title": title,
            "revision_id": document.get("revisionId"),
            **drive_meta,
        }

        return content, metadata

    def _extract_text_from_document(self, document: Dict) -> str:
        """Convert Google Docs structure to plain text."""
        text_parts = []
        body = document.get("body", {})
        content = body.get("content", [])

        for element in content:
            if "paragraph" in element:
                para_text = ""
                for elem in element["paragraph"].get("elements", []):
                    if "textRun" in elem:
                        para_text += elem["textRun"].get("content", "")
                text_parts.append(para_text)
            elif "table" in element:
                text_parts.append("[TABLE]")

        return "".join(text_parts)

    def _extract_sheets(self, sheet_id: str, filename: str) -> Tuple[str, Dict[str, Any]]:
        """Extract Google Sheets content via Sheets API."""
        spreadsheet = self._sheets_service.spreadsheets().get(
            spreadsheetId=sheet_id
        ).execute()
        drive_meta = self._get_drive_metadata(sheet_id)

        title = spreadsheet.get("properties", {}).get("title", filename)
        sheets = spreadsheet.get("sheets", [])
        sheet_names = [s["properties"]["title"] for s in sheets]

        # Get data from first sheet (first 100 rows)
        content_parts = [f"# {title}\n"]
        preview_data = []

        if sheet_names:
            try:
                result = self._sheets_service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=f"'{sheet_names[0]}'!A1:Z100"
                ).execute()
                values = result.get("values", [])
                if values:
                    content_parts.append(f"\n## Sheet: {sheet_names[0]}\n")
                    for row in values[:20]:  # Limit preview to 20 rows
                        content_parts.append(" | ".join(str(cell) for cell in row) + "\n")
                    preview_data = values[:5]
            except Exception as e:
                logger.warning(f"Failed to get sheet values: {e}")

        metadata = {
            "extraction_method": "google_sheets_api",
            "file_type": "gsheet",
            "document_id": sheet_id,
            "title": title,
            "sheet_count": len(sheets),
            "sheet_names": sheet_names,
            "preview_rows": len(preview_data),
            **drive_meta,
        }

        return "".join(content_parts), metadata

    def _extract_slides(self, presentation_id: str, filename: str) -> Tuple[str, Dict[str, Any]]:
        """Extract Google Slides content via Slides API."""
        presentation = self._slides_service.presentations().get(
            presentationId=presentation_id
        ).execute()
        drive_meta = self._get_drive_metadata(presentation_id)

        title = presentation.get("title", filename)
        slides = presentation.get("slides", [])

        content_parts = [f"# {title}\n\n"]
        slide_texts = []

        for idx, slide in enumerate(slides, 1):
            slide_text = f"## Slide {idx}\n"
            texts = []
            for element in slide.get("pageElements", []):
                if "shape" in element:
                    shape = element["shape"]
                    if "text" in shape:
                        text_elements = shape["text"].get("textElements", [])
                        for te in text_elements:
                            if "textRun" in te:
                                texts.append(te["textRun"].get("content", ""))
            if texts:
                slide_text += "".join(texts) + "\n"
            content_parts.append(slide_text)
            slide_texts.append("".join(texts).strip())

        metadata = {
            "extraction_method": "google_slides_api",
            "file_type": "gslides",
            "document_id": presentation_id,
            "title": title,
            "slide_count": len(slides),
            "slide_texts": slide_texts[:10],  # First 10 slides text preview
            **drive_meta,
        }

        return "".join(content_parts), metadata

    def _extract_forms(self, form_id: str, filename: str) -> Tuple[str, Dict[str, Any]]:
        """Extract Google Forms structure via Forms API."""
        form = self._forms_service.forms().get(formId=form_id).execute()
        drive_meta = self._get_drive_metadata(form_id)

        info = form.get("info", {})
        title = info.get("title", filename)
        description = info.get("description", "")
        items = form.get("items", [])

        content_parts = [f"# {title}\n"]
        if description:
            content_parts.append(f"\n{description}\n")

        questions = []
        content_parts.append("\n## Questions\n")
        for item in items:
            item_title = item.get("title", "Untitled")
            content_parts.append(f"- {item_title}\n")
            question_info = {"title": item_title, "item_id": item.get("itemId")}
            if "questionItem" in item:
                q = item["questionItem"].get("question", {})
                question_info["required"] = q.get("required", False)
            questions.append(question_info)

        metadata = {
            "extraction_method": "google_forms_api",
            "file_type": "gform",
            "document_id": form_id,
            "title": title,
            "description": description,
            "question_count": len(questions),
            "questions": questions[:20],  # First 20 questions
            **drive_meta,
        }

        return "".join(content_parts), metadata

    def _extract_drawings(self, drawing_id: str, filename: str) -> Tuple[str, Dict[str, Any]]:
        """Extract Google Drawings metadata (no dedicated content API)."""
        drive_meta = self._get_drive_metadata(drawing_id)
        title = drive_meta.get("title", filename)

        content = f"# {title}\n\nGoogle Drawing (visual content cannot be extracted as text)"

        metadata = {
            "extraction_method": "google_drive_api",
            "file_type": "gdraw",
            "document_id": drawing_id,
            "title": title,
            **drive_meta,
        }

        return content, metadata

    def _extract_fallback(
        self, doc_id: str, ext: str, filename: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Fallback extraction using Drive API only."""
        drive_meta = self._get_drive_metadata(doc_id)
        title = drive_meta.get("title", filename)
        type_label = self._get_type_label(ext)

        return f"{type_label}: {title}", {
            "extraction_method": "google_drive_api",
            "file_type": ext,
            "document_id": doc_id,
            **drive_meta,
        }
