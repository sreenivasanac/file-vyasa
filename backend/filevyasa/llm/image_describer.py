"""LLM-based image description generator using Ollama llava model."""

import base64
from datetime import datetime
from mimetypes import guess_type
from pathlib import Path

import structlog

from filevyasa.models.file_object import FileObject
from filevyasa.models.enums import FilenameQuality

logger = structlog.get_logger()


IMAGE_DESCRIPTION_PROMPT_TEMPLATE = """You are an image analysis assistant. Analyze this image.

Current filename: {filename}

Provide:
1. A brief summary (1-2 sentences): Main subject/content of this image?
2. A detailed description (2-4 sentences): Describe the scene, notable objects,
   colors, composition, and any relevant context.
3. Filename assessment: Evaluate the current filename and suggest a better one if needed.
   - "good": Descriptive, meaningful name (e.g., "sunset_beach_hawaii_2024.jpg", "family_reunion_thanksgiving.png")
   - "acceptable": Adequate but could be improved (e.g., "beach_photo.jpg", "screenshot.png")
   - "poor": Vague or unhelpful (e.g., "photo1.jpg", "image.png", "pic.jpg")
   - "meaningless": Arbitrary/auto-generated name (e.g., "IMG_0001.jpg", "DSC_1234.png", "Untitled.png", "download.jpg", "Screen Shot 2024-01-01.png")

Respond in this exact JSON format:
{{
    "brief_summary": "...",
    "detailed_summary": "...",
    "filename_quality": "good|acceptable|poor|meaningless",
    "suggested_filename": "descriptive_name.ext (always provide a suggestion based on image content)"
}}
"""


class ImageDescriber:
    """Generate AI descriptions for images using Ollama llava model.

    This class exclusively uses Ollama's llava model for image descriptions.
    It does not use the user's configured LLM model.
    """

    LLAVA_MODEL = "ollama/llava:latest"
    OLLAMA_API_BASE = "http://localhost:11434"

    SUPPORTED_IMAGE_EXTENSIONS = [
        "jpg", "jpeg", "png", "gif", "bmp", "webp"
    ]

    def __init__(self):
        self._litellm = None

    def _get_litellm(self):
        """Lazy load litellm."""
        if self._litellm is None:
            import litellm
            self._litellm = litellm
        return self._litellm

    def _encode_image(self, file_path: Path) -> tuple[str, str]:
        """Encode image to base64 and determine MIME type."""
        mime_type, _ = guess_type(str(file_path))
        if mime_type is None:
            ext = file_path.suffix.lower()
            mime_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".bmp": "image/bmp",
                ".webp": "image/webp",
            }
            mime_type = mime_map.get(ext, "image/jpeg")

        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        return image_data, mime_type

    def describe(self, file_obj: FileObject) -> FileObject:
        """Generate AI description for an image file using Ollama llava.

        Args:
            file_obj: FileObject representing an image

        Returns:
            FileObject with ai_brief_summary and ai_summary populated
        """
        litellm = self._get_litellm()

        file_path = Path(file_obj.path)

        if not file_path.exists():
            logger.warning("image_not_found", path=str(file_path))
            file_obj.ai_brief_summary = "[Image file not found]"
            return file_obj

        ext = file_path.suffix.lower().lstrip(".")
        if ext not in self.SUPPORTED_IMAGE_EXTENSIONS:
            logger.debug("unsupported_image_format", extension=ext)
            file_obj.ai_brief_summary = f"[Unsupported image format: {ext}]"
            return file_obj

        try:
            image_data, mime_type = self._encode_image(file_path)

            # Build prompt with filename
            prompt = IMAGE_DESCRIPTION_PROMPT_TEMPLATE.format(filename=file_obj.filename)

            # Always use Ollama llava for image descriptions
            kwargs = {
                "model": self.LLAVA_MODEL,
                "api_base": self.OLLAMA_API_BASE,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 600,
            }

            response = litellm.completion(**kwargs)

            content = response.choices[0].message.content
            result = self._parse_response(content, file_obj.extension)

            file_obj.ai_brief_summary = result.get("brief_summary", "")
            file_obj.ai_summary = result.get("detailed_summary", "")
            file_obj.filename_quality = result.get("filename_quality")
            file_obj.suggested_filename = result.get("suggested_filename")
            file_obj.llm_model = self.LLAVA_MODEL
            file_obj.summarized_at = datetime.now()

            logger.info(
                "image_described",
                filename=file_obj.filename,
                model=self.LLAVA_MODEL,
                filename_quality=file_obj.filename_quality,
            )

        except Exception as e:
            logger.error("image_description_failed", filename=file_obj.filename, error=str(e))
            file_obj.ai_brief_summary = f"[Image description failed: {str(e)[:100]}]"
            file_obj.ai_summary = ""

        return file_obj

    def _parse_response(self, content: str, file_extension: str) -> dict:
        """Parse JSON response from LLM."""
        import json
        import re

        valid_qualities = {"good", "acceptable", "poor", "meaningless"}

        def normalize_keys(data: dict, ext: str) -> dict:
            """Normalize keys and validate values."""
            result = {
                "brief_summary": "",
                "detailed_summary": "",
                "filename_quality": None,
                "suggested_filename": None,
            }
            if "brief_summary" in data:
                result["brief_summary"] = data["brief_summary"]
            if "detailed_summary" in data:
                result["detailed_summary"] = data["detailed_summary"]
            elif "detailed_description" in data:
                result["detailed_summary"] = data["detailed_description"]

            # Handle filename quality
            quality = data.get("filename_quality", "").lower().strip()
            if quality in valid_qualities:
                result["filename_quality"] = FilenameQuality(quality)

            # Handle suggested filename - ensure it has the right extension
            suggested = data.get("suggested_filename")
            if suggested and isinstance(suggested, str):
                suggested = suggested.strip()
                # Ensure suggested filename has the correct extension
                if ext and not suggested.lower().endswith(f".{ext.lower()}"):
                    suggested = f"{suggested.rsplit('.', 1)[0]}.{ext}" if '.' in suggested else f"{suggested}.{ext}"
                result["suggested_filename"] = suggested

            return result

        try:
            parsed = json.loads(content)
            return normalize_keys(parsed, file_extension)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                return normalize_keys(parsed, file_extension)
            except json.JSONDecodeError:
                pass

        json_match = re.search(r'\{[^{}]*"brief_summary"[^{}]*\}', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                return normalize_keys(parsed, file_extension)
            except json.JSONDecodeError:
                pass

        brief_match = re.search(r'"brief_summary"\s*:\s*"([^"]*)"', content)
        detailed_match = re.search(r'"detailed_(?:summary|description)"\s*:\s*"([^"]*)"', content)
        quality_match = re.search(r'"filename_quality"\s*:\s*"([^"]*)"', content)
        suggested_match = re.search(r'"suggested_filename"\s*:\s*"([^"]*)"', content)

        if brief_match or detailed_match:
            quality_val = quality_match.group(1).lower() if quality_match else None
            return {
                "brief_summary": brief_match.group(1) if brief_match else "",
                "detailed_summary": detailed_match.group(1) if detailed_match else "",
                "filename_quality": FilenameQuality(quality_val) if quality_val in valid_qualities else None,
                "suggested_filename": suggested_match.group(1) if suggested_match else None,
            }

        cleaned = re.sub(r'[{}":]', '', content).strip()
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]

        return {
            "brief_summary": lines[0] if lines else content[:100],
            "detailed_summary": ' '.join(lines[:3]) if lines else content[:200],
            "filename_quality": None,
            "suggested_filename": None,
        }
