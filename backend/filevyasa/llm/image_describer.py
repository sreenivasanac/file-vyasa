"""LLM-based image description generator using Ollama llava model."""

import base64
from datetime import datetime
from mimetypes import guess_type
from pathlib import Path

import structlog

from filevyasa.models.file_object import FileObject

logger = structlog.get_logger()


IMAGE_DESCRIPTION_PROMPT = """You are an image analysis assistant. Analyze this image.

Provide:
1. A brief summary (1-2 sentences): Main subject/content of this image?
2. A detailed description (2-4 sentences): Describe the scene, notable objects,
   colors, composition, and any relevant context.

Respond in this exact JSON format:
{
    "brief_summary": "...",
    "detailed_summary": "..."
}
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

            # Always use Ollama llava for image descriptions
            kwargs = {
                "model": self.LLAVA_MODEL,
                "api_base": self.OLLAMA_API_BASE,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": IMAGE_DESCRIPTION_PROMPT},
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
                "max_tokens": 500,
            }

            response = litellm.completion(**kwargs)

            content = response.choices[0].message.content
            result = self._parse_response(content)

            file_obj.ai_brief_summary = result.get("brief_summary", "")
            file_obj.ai_summary = result.get("detailed_summary", "")
            file_obj.llm_model = self.LLAVA_MODEL
            file_obj.summarized_at = datetime.now()

            logger.info("image_described", filename=file_obj.filename, model=self.LLAVA_MODEL)

        except Exception as e:
            logger.error("image_description_failed", filename=file_obj.filename, error=str(e))
            file_obj.ai_brief_summary = f"[Image description failed: {str(e)[:100]}]"
            file_obj.ai_summary = ""

        return file_obj

    def _parse_response(self, content: str) -> dict:
        """Parse JSON response from LLM."""
        import json
        import re

        def normalize_keys(data: dict) -> dict:
            """Normalize keys - handle detailed_description vs detailed_summary."""
            result = {"brief_summary": "", "detailed_summary": ""}
            if "brief_summary" in data:
                result["brief_summary"] = data["brief_summary"]
            if "detailed_summary" in data:
                result["detailed_summary"] = data["detailed_summary"]
            elif "detailed_description" in data:
                result["detailed_summary"] = data["detailed_description"]
            return result

        try:
            parsed = json.loads(content)
            return normalize_keys(parsed)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                return normalize_keys(parsed)
            except json.JSONDecodeError:
                pass

        json_match = re.search(r'\{[^{}]*"brief_summary"[^{}]*\}', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                return normalize_keys(parsed)
            except json.JSONDecodeError:
                pass

        brief_match = re.search(r'"brief_summary"\s*:\s*"([^"]*)"', content)
        detailed_match = re.search(r'"detailed_(?:summary|description)"\s*:\s*"([^"]*)"', content)

        if brief_match or detailed_match:
            return {
                "brief_summary": brief_match.group(1) if brief_match else "",
                "detailed_summary": detailed_match.group(1) if detailed_match else ""
            }

        cleaned = re.sub(r'[{}":]', '', content).strip()
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]

        return {
            "brief_summary": lines[0] if lines else content[:100],
            "detailed_summary": ' '.join(lines[:3]) if lines else content[:200]
        }
