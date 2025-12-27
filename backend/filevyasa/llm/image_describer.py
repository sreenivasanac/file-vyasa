"""LLM-based image description generator using Ollama llava model."""

import base64
from datetime import datetime
from mimetypes import guess_type
from pathlib import Path

import structlog

from filevyasa.llm.response_parser import parse_llm_response
from filevyasa.models.file_object import FileObject

logger = structlog.get_logger()


IMAGE_DESCRIPTION_PROMPT_TEMPLATE = """You are an image analysis assistant. Analyze this image.

Current filename: {filename}

Provide:
1. A brief summary (1-2 sentences): Main subject/content of this image?
2. A detailed description (2-4 sentences): Describe the scene, notable objects,
   colors, composition, and any relevant context.
3. Filename assessment: Evaluate the current filename and suggest a better one if needed.
   - "good": Descriptive, meaningful name (e.g.,
     "Discharge Summary Sakra Hospital.pdf",
     "Resume_John_adams.pdf",
     "i140_rec_by_class_country_fy2024_q3.xlsx",
     "Driving License_Virginia.pdf",
     "dreber-et-al-2015-using-prediction-markets.pdf")
   - "acceptable": Adequate but could be improved (e.g., "beach_photo.jpg", "pancard.jpeg")
   - "poor": Vague, generic names or computer generated IDs (e.g.,
     "photo1.jpg", "image.png", "IMG_0001.jpg", "DSC_1234.png",
     "ssstwitter.com_1764435559460.mp4",
     "WhatsApp Image 2025-07-22 at 17.38.01.jpeg",
     "Screenshot 2025-10-28 at 1.24 AM.png")
   - "meaningless": Arbitrary, unhelpful name (e.g. "Untitled.pdf", "HyL793zMncZV_HxE.mp4")

Respond in this exact JSON format:
{{
    "brief_summary": "...",
    "detailed_summary": "...",
    "filename_quality": "good|acceptable|poor|meaningless",
    "suggested_filename": "descriptive_name.ext (based on image content)"
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
        "jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "tif"
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
                ".tiff": "image/tiff",
                ".tif": "image/tiff",
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
            result = parse_llm_response(content, file_obj.extension)

            file_obj.ai_brief_summary = result.brief_summary
            file_obj.ai_summary = result.detailed_summary
            file_obj.filename_quality = result.filename_quality
            file_obj.suggested_filename = result.suggested_filename
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
