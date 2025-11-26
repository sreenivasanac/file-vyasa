"""Configuration API endpoints."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from filevyasa.config import settings

router = APIRouter()


class LLMConfigRequest(BaseModel):
    """Request to update LLM configuration."""

    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None


class LLMConfigResponse(BaseModel):
    """Response with LLM configuration (without sensitive data)."""

    provider: str
    model: str
    api_base: Optional[str]
    api_key_configured: bool


class AppConfigResponse(BaseModel):
    """Response with application configuration."""

    app_name: str
    version: str
    debug: bool
    db_path: str
    max_content_lines: int
    default_ignore_patterns: list[str]
    llm: LLMConfigResponse


@router.get("/", response_model=AppConfigResponse)
async def get_config():
    """Get current application configuration."""
    return AppConfigResponse(
        app_name=settings.app_name,
        version="1.1.0",
        debug=settings.debug,
        db_path=str(settings.db_path),
        max_content_lines=settings.max_content_lines,
        default_ignore_patterns=settings.default_ignore_patterns,
        llm=LLMConfigResponse(
            provider=settings.llm_provider,
            model=settings.llm_model,
            api_base=settings.llm_api_base,
            api_key_configured=bool(settings.llm_api_key),
        ),
    )


@router.post("/llm", response_model=LLMConfigResponse)
async def update_llm_config(config: LLMConfigRequest):
    """
    Update LLM configuration for the current session.

    Note: This updates the in-memory settings only.
    For persistence, use environment variables or .env file.
    """
    if config.provider:
        settings.llm_provider = config.provider
    if config.model:
        settings.llm_model = config.model
    if config.api_key:
        settings.llm_api_key = config.api_key
    if config.api_base:
        settings.llm_api_base = config.api_base

    return LLMConfigResponse(
        provider=settings.llm_provider,
        model=settings.llm_model,
        api_base=settings.llm_api_base,
        api_key_configured=bool(settings.llm_api_key),
    )


@router.get("/supported-extensions")
async def get_supported_extensions():
    """Get list of supported file extensions for extraction."""
    from filevyasa.extractor import DocumentExtractor, ImageExtractor, TextExtractor

    return {
        "text": TextExtractor.supported_extensions(),
        "document": DocumentExtractor.supported_extensions(),
        "image": ImageExtractor.supported_extensions(),
    }


class LlavaStatusResponse(BaseModel):
    """Response for llava model availability check."""
    available: bool
    reason: Optional[str] = None


@router.get("/llava-status", response_model=LlavaStatusResponse)
async def check_llava_status():
    """Check if Ollama llava model is available for image descriptions."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                return LlavaStatusResponse(
                    available=False,
                    reason="Ollama is not running. Start it with: ollama serve"
                )

            models = response.json().get("models", [])
            llava_available = any(
                m.get("name", "").startswith("llava")
                for m in models
            )

            if llava_available:
                return LlavaStatusResponse(available=True, reason=None)
            else:
                return LlavaStatusResponse(
                    available=False,
                    reason="llava model not installed. Run: ollama pull llava"
                )

    except httpx.ConnectError:
        return LlavaStatusResponse(
            available=False,
            reason="Cannot connect to Ollama. Start it with: ollama serve"
        )
    except Exception as e:
        return LlavaStatusResponse(
            available=False,
            reason=f"Error checking Ollama: {str(e)}"
        )
