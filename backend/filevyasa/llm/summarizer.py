"""LLM-based file summarizer using LiteLLM."""

from datetime import datetime
from typing import Optional

import structlog

from filevyasa.config import settings
from filevyasa.models.file_object import FileObject

logger = structlog.get_logger()


SUMMARY_PROMPT_TEMPLATE = """You are a file organization assistant. Analyze the following file information and provide summaries.

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
1. A brief summary (2 lines max) that captures the essence of this file - what it is and what it's about.
2. A detailed summary (4 lines max) with more context about the content, purpose, and any notable details.

Respond in this exact JSON format:
{{
    "brief_summary": "...",
    "detailed_summary": "..."
}}
"""


class Summarizer:
    """LLM-based file summarizer using LiteLLM."""
    
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None
    ):
        """
        Initialize the summarizer.
        
        Args:
            model: LLM model name (default from settings)
            api_key: API key (default from settings)
            api_base: Custom API base URL (default from settings)
        """
        self.model = model or settings.llm_model
        self.api_key = api_key or settings.llm_api_key
        self.api_base = api_base or settings.llm_api_base
        
        self._litellm = None
    
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
            # Build completion kwargs
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful file organization assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 500,
                "response_format": {"type": "json_object"}
            }
            
            if self.api_base:
                kwargs["api_base"] = self.api_base
            
            response = litellm.completion(**kwargs)
            
            # Parse response
            content = response.choices[0].message.content
            result = self._parse_response(content)
            
            file_obj.ai_brief_summary = result.get("brief_summary", "")
            file_obj.ai_summary = result.get("detailed_summary", "")
            file_obj.summarized_at = datetime.now()
            
            logger.info("file_summarized", filename=file_obj.filename)
            
        except Exception as e:
            logger.error("summarization_failed", filename=file_obj.filename, error=str(e))
            file_obj.ai_brief_summary = f"[Summarization failed: {str(e)[:100]}]"
            file_obj.ai_summary = ""
        
        return file_obj
    
    def _parse_response(self, content: str) -> dict:
        """Parse JSON response from LLM."""
        import json
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract from text if JSON parsing fails
            return {
                "brief_summary": content[:200],
                "detailed_summary": content[:400]
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
