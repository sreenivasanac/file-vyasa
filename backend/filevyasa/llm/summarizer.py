"""LLM-based file summarizer using LiteLLM."""

from datetime import datetime

import structlog

from filevyasa.config import settings
from filevyasa.models.enums import FilenameQuality
from filevyasa.models.file_object import FileObject

logger = structlog.get_logger()


SUMMARY_PROMPT_TEMPLATE = """You are a file organization assistant. \
Analyze the following file information and provide summaries.

File Information:
- Filename: {filename}
- Type: {extension} ({mime_type})
- Category: {category}
- Size: {size_human}
- Created: {created_at}
- Modified: {modified_at}

Content Preview:
{content_preview}

Additional Metadata:
{metadata}

Please provide:
1. A brief summary (2 lines max) capturing the essence - what it is and about.
2. A detailed summary (4 lines max) with more context about content and purpose.
3. Filename assessment: Evaluate the current filename and suggest a better one if needed.
   - "good": Descriptive, meaningful name (e.g., "Q3_2024_Financial_Report.xlsx")
   - "acceptable": Adequate but could be improved (e.g., "report.docx", "notes.txt")
   - "poor": Vague or unhelpful (e.g., "doc1.pdf", "file.docx", "new.txt")
   - "meaningless": Arbitrary/auto-generated name (e.g., "Untitled.docx", "Document1.pdf")

Respond in this exact JSON format:
{{
    "brief_summary": "...",
    "detailed_summary": "...",
    "filename_quality": "good|acceptable|poor|meaningless",
    "suggested_filename": "descriptive_name.ext"
}}
"""


class Summarizer:
    """LLM-based file summarizer using LiteLLM."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None
    ):
        """
        Initialize the summarizer.

        Args:
            provider: LLM provider (ollama, openai, anthropic, etc.)
            model: LLM model name (default from settings)
            api_key: API key (default from settings)
            api_base: Custom API base URL (default from settings)
        """
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.api_key = api_key or settings.llm_api_key
        self.api_base = api_base or settings.llm_api_base

        self._litellm = None

    def _get_model_name(self) -> str:
        """Get the model name formatted for LiteLLM based on provider.

        LiteLLM uses provider prefixes to route requests. See:
        https://docs.litellm.ai/docs/providers
        """
        # Providers that need prefix for LiteLLM routing
        PREFIXED_PROVIDERS = {
            "ollama": "ollama/",
            "anthropic": "anthropic/",
            "gemini": "gemini/",
            "groq": "groq/",
            "deepseek": "deepseek/",
            "together_ai": "together_ai/",
            "fireworks_ai": "fireworks_ai/",
        }

        prefix = PREFIXED_PROVIDERS.get(self.provider, "")
        if prefix and not self.model.startswith(prefix):
            return f"{prefix}{self.model}"

        # OpenAI models don't need prefix
        return self.model

    def _get_litellm(self):
        """Lazy load litellm."""
        if self._litellm is None:
            import litellm
            self._litellm = litellm

            # Configure API key if provided
            if self.api_key:
                litellm.api_key = self.api_key
        return self._litellm

    def summarize(self, file_obj: FileObject) -> FileObject:
        """
        Generate AI summaries for a file object.

        Args:
            file_obj: FileObject with content_preview populated

        Returns:
            FileObject with ai_brief_summary and ai_summary populated
        """
        litellm = self._get_litellm()

        # Build the prompt
        prompt = SUMMARY_PROMPT_TEMPLATE.format(
            filename=file_obj.filename,
            extension=file_obj.extension,
            mime_type=file_obj.mime_type,
            category=file_obj.category.value,
            size_human=file_obj.size_human,
            created_at=file_obj.created_at.isoformat() if file_obj.created_at else "Unknown",
            modified_at=file_obj.modified_at.isoformat() if file_obj.modified_at else "Unknown",
            content_preview=file_obj.content_preview[:2000],  # Limit content
            metadata=str(file_obj.metadata)[:500],  # Limit metadata
        )

        try:
            # Get properly formatted model name for LiteLLM
            model_name = self._get_model_name()

            # Build completion kwargs
            system_msg = (
                "You are a helpful file organization assistant. "
                "Always respond with valid JSON."
            )
            kwargs = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 600,
            }

            # Only add response_format for providers that support it (OpenAI, etc.)
            # Ollama and some other providers don't support structured JSON output mode
            if self.provider in ("openai", "azure"):
                kwargs["response_format"] = {"type": "json_object"}

            if self.api_base:
                kwargs["api_base"] = self.api_base

            response = litellm.completion(**kwargs)

            # Parse response
            content = response.choices[0].message.content
            result = self._parse_response(content, file_obj.extension)

            file_obj.ai_brief_summary = result.get("brief_summary", "")
            file_obj.ai_summary = result.get("detailed_summary", "")
            file_obj.filename_quality = result.get("filename_quality")
            file_obj.suggested_filename = result.get("suggested_filename")
            file_obj.llm_model = model_name  # Store which model was used
            file_obj.summarized_at = datetime.now()

            logger.info(
                "file_summarized",
                filename=file_obj.filename,
                filename_quality=file_obj.filename_quality,
            )

        except Exception as e:
            logger.error("summarization_failed", filename=file_obj.filename, error=str(e))
            file_obj.ai_brief_summary = f"[Summarization failed: {str(e)[:100]}]"
            file_obj.ai_summary = ""

        return file_obj

    def _parse_response(self, content: str, file_extension: str) -> dict:
        """Parse JSON response from LLM.

        Handles various response formats:
        - Clean JSON
        - JSON wrapped in markdown code blocks
        - Regex extraction as fallback
        """
        import json
        import re

        valid_qualities = {"good", "acceptable", "poor", "meaningless"}

        def normalize_result(data: dict, ext: str) -> dict:
            """Normalize and validate parsed data."""
            result = {
                "brief_summary": data.get("brief_summary", ""),
                "detailed_summary": data.get("detailed_summary", ""),
                "filename_quality": None,
                "suggested_filename": None,
            }

            # Handle filename quality
            quality = str(data.get("filename_quality", "")).lower().strip()
            if quality in valid_qualities:
                result["filename_quality"] = FilenameQuality(quality)

            # Handle suggested filename - ensure it has the right extension
            suggested = data.get("suggested_filename")
            if suggested and isinstance(suggested, str):
                suggested = suggested.strip()
                # Ensure suggested filename has the correct extension
                if ext and not suggested.lower().endswith(f".{ext.lower()}"):
                    base = suggested.rsplit('.', 1)[0] if '.' in suggested else suggested
                    suggested = f"{base}.{ext}"
                result["suggested_filename"] = suggested

            return result

        # Try direct JSON parsing first
        try:
            parsed = json.loads(content)
            return normalize_result(parsed, file_extension)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                return normalize_result(parsed, file_extension)
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in the text
        json_match = re.search(r'\{[^{}]*"brief_summary"[^{}]*\}', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                return normalize_result(parsed, file_extension)
            except json.JSONDecodeError:
                pass

        # Try regex extraction of values
        brief_match = re.search(r'"brief_summary"\s*:\s*"([^"]*)"', content)
        detailed_match = re.search(r'"detailed_summary"\s*:\s*"([^"]*)"', content)
        quality_match = re.search(r'"filename_quality"\s*:\s*"([^"]*)"', content)
        suggested_match = re.search(r'"suggested_filename"\s*:\s*"([^"]*)"', content)

        if brief_match or detailed_match:
            quality_val = quality_match.group(1).lower() if quality_match else None
            return {
                "brief_summary": brief_match.group(1) if brief_match else "",
                "detailed_summary": detailed_match.group(1) if detailed_match else "",
                "filename_quality": (
                    FilenameQuality(quality_val) if quality_val in valid_qualities else None
                ),
                "suggested_filename": suggested_match.group(1) if suggested_match else None,
            }

        # Last resort: treat the whole content as a summary (cleaned)
        # Remove any JSON-like formatting
        cleaned = re.sub(r'[{}":]', '', content).strip()
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]

        return {
            "brief_summary": lines[0] if lines else content[:100],
            "detailed_summary": ' '.join(lines[:3]) if lines else content[:200],
            "filename_quality": None,
            "suggested_filename": None,
        }


def summarize_file(
    file_obj: FileObject,
    model: str | None = None,
    api_key: str | None = None
) -> FileObject:
    """
    Convenience function to summarize a single file.

    Args:
        file_obj: FileObject to summarize
        model: Optional model override
        api_key: Optional API key override

    Returns:
        FileObject with summaries populated
    """
    summarizer = Summarizer(model=model, api_key=api_key)
    return summarizer.summarize(file_obj)
