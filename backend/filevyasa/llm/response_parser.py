"""Shared LLM response parsing utilities."""

import json
import re

from pydantic import BaseModel, field_validator

from filevyasa.models.enums import FilenameQuality


class LLMSummaryResponse(BaseModel):
    """Pydantic model for LLM summary responses."""

    brief_summary: str = ""
    detailed_summary: str = ""
    filename_quality: FilenameQuality | None = None
    suggested_filename: str | None = None

    @field_validator("filename_quality", mode="before")
    @classmethod
    def normalize_quality(cls, v):
        """Normalize filename quality to enum."""
        if v is None:
            return None
        if isinstance(v, FilenameQuality):
            return v
        if isinstance(v, str):
            v = v.lower().strip()
            if v in {"good", "acceptable", "poor", "meaningless"}:
                return FilenameQuality(v)
        return None


def _extract_json_from_content(content: str) -> dict | None:
    """Try to extract JSON from LLM response content."""
    # Try direct JSON parsing
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in the text
    json_match = re.search(r'\{[^{}]*"brief_summary"[^{}]*\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _extract_fields_via_regex(content: str) -> dict | None:
    """Extract individual fields using regex as fallback."""
    brief_match = re.search(r'"brief_summary"\s*:\s*"([^"]*)"', content)
    detailed_match = re.search(r'"detailed_(?:summary|description)"\s*:\s*"([^"]*)"', content)
    quality_match = re.search(r'"filename_quality"\s*:\s*"([^"]*)"', content)
    suggested_match = re.search(r'"suggested_filename"\s*:\s*"([^"]*)"', content)

    if brief_match or detailed_match:
        return {
            "brief_summary": brief_match.group(1) if brief_match else "",
            "detailed_summary": detailed_match.group(1) if detailed_match else "",
            "filename_quality": quality_match.group(1) if quality_match else None,
            "suggested_filename": suggested_match.group(1) if suggested_match else None,
        }
    return None


def _fallback_parse(content: str) -> dict:
    """Last resort: treat content as plain text summary."""
    cleaned = re.sub(r'[{}":]', '', content).strip()
    lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
    return {
        "brief_summary": lines[0] if lines else content[:100],
        "detailed_summary": ' '.join(lines[:3]) if lines else content[:200],
        "filename_quality": None,
        "suggested_filename": None,
    }


def _ensure_extension(filename: str | None, extension: str) -> str | None:
    """Ensure suggested filename has the correct extension."""
    if not filename or not isinstance(filename, str):
        return None
    filename = filename.strip()
    if extension and not filename.lower().endswith(f".{extension.lower()}"):
        base = filename.rsplit('.', 1)[0] if '.' in filename else filename
        filename = f"{base}.{extension}"
    return filename


def parse_llm_response(content: str, file_extension: str) -> LLMSummaryResponse:
    """Parse LLM response into a structured LLMSummaryResponse.

    Handles various response formats with fallbacks:
    1. Clean JSON
    2. JSON wrapped in markdown code blocks
    3. Regex extraction of individual fields
    4. Plain text fallback

    Args:
        content: Raw LLM response content
        file_extension: File extension to ensure on suggested filename

    Returns:
        LLMSummaryResponse with parsed fields
    """
    # Handle "detailed_description" as alias for "detailed_summary"
    def normalize_data(data: dict) -> dict:
        if "detailed_description" in data and "detailed_summary" not in data:
            data["detailed_summary"] = data.pop("detailed_description")
        return data

    # Try JSON extraction
    data = _extract_json_from_content(content)
    if data:
        data = normalize_data(data)
        data["suggested_filename"] = _ensure_extension(
            data.get("suggested_filename"), file_extension
        )
        return LLMSummaryResponse.model_validate(data)

    # Try regex extraction
    data = _extract_fields_via_regex(content)
    if data:
        data["suggested_filename"] = _ensure_extension(
            data.get("suggested_filename"), file_extension
        )
        return LLMSummaryResponse.model_validate(data)

    # Fallback to plain text
    data = _fallback_parse(content)
    return LLMSummaryResponse.model_validate(data)
