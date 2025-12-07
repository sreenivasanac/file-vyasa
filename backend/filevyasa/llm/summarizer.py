"""LLM-based file summarizer using LiteLLM."""

from datetime import datetime

import structlog

from filevyasa.config import settings
from filevyasa.llm.response_parser import parse_llm_response
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

            # Parse response using shared parser
            content = response.choices[0].message.content
            result = parse_llm_response(content, file_obj.extension)

            file_obj.ai_brief_summary = result.brief_summary
            file_obj.ai_summary = result.detailed_summary
            file_obj.filename_quality = result.filename_quality
            file_obj.suggested_filename = result.suggested_filename
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
