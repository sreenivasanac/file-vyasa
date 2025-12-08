"""Configuration API endpoints."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from filevyasa.config import settings, update_local_config_setting

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


class GoogleConfigRequest(BaseModel):
    """Request to update Google credentials configuration."""

    credentials_path: Optional[str] = None


class GoogleConfigResponse(BaseModel):
    """Response with Google credentials configuration."""

    credentials_configured: bool
    credentials_path: Optional[str] = None


class AppConfigResponse(BaseModel):
    """Response with application configuration."""

    app_name: str
    version: str
    debug: bool
    db_path: str
    max_content_lines: int
    default_ignore_patterns: list[str]
    llm: LLMConfigResponse
    google: GoogleConfigResponse


@router.get("/", response_model=AppConfigResponse)
async def get_config():
    """Get current application configuration."""
    # Combine file patterns and folder names for backward compatibility
    all_ignore_patterns = list(settings.ignore_file_patterns) + list(settings.ignore_folder_names)
    return AppConfigResponse(
        app_name=settings.app_name,
        version="1.1.0",
        debug=settings.debug,
        db_path=str(settings.db_path),
        max_content_lines=settings.max_content_lines,
        default_ignore_patterns=all_ignore_patterns,
        llm=LLMConfigResponse(
            provider=settings.llm_provider,
            model=settings.llm_model,
            api_base=settings.llm_api_base,
            api_key_configured=bool(settings.llm_api_key),
        ),
        google=GoogleConfigResponse(
            credentials_configured=bool(settings.google_credentials_path),
            credentials_path=settings.google_credentials_path,
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


@router.post("/google", response_model=GoogleConfigResponse)
async def update_google_config(config: GoogleConfigRequest):
    """
    Update Google Workspace credentials configuration.

    Persists the credentials path to .filevyasa/local_config.json.
    """
    if config.credentials_path is not None:
        new_path = config.credentials_path if config.credentials_path else None
        settings.google_credentials_path = new_path
        update_local_config_setting("google_credentials_path", new_path)

    return GoogleConfigResponse(
        credentials_configured=bool(settings.google_credentials_path),
        credentials_path=settings.google_credentials_path,
    )


class GoogleVerifyResponse(BaseModel):
    """Response for Google credentials verification."""

    success: bool
    message: str
    service_account_email: Optional[str] = None


@router.post("/google/verify", response_model=GoogleVerifyResponse)
async def verify_google_credentials():
    """Verify Google Workspace credentials by attempting to authenticate."""
    from pathlib import Path

    credentials_path = settings.google_credentials_path
    if not credentials_path:
        return GoogleVerifyResponse(
            success=False,
            message="No credentials path configured. Please select a credentials file first."
        )

    credentials_file = Path(credentials_path)
    if not credentials_file.exists():
        return GoogleVerifyResponse(
            success=False,
            message=f"Credentials file not found: {credentials_path}"
        )

    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return GoogleVerifyResponse(
            success=False,
            message="Google API libraries not installed. "
            "Install with: pip install google-api-python-client google-auth"
        )

    try:
        scopes = [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/documents.readonly",
        ]
        credentials = Credentials.from_service_account_file(
            str(credentials_file), scopes=scopes
        )

        # Try to build Drive service and make a simple API call
        drive_service = build("drive", "v3", credentials=credentials)
        # Just try to get about info - this validates credentials work
        drive_service.about().get(fields="user").execute()

        return GoogleVerifyResponse(
            success=True,
            message="Successfully authenticated with Google Workspace APIs",
            service_account_email=credentials.service_account_email
        )
    except Exception as e:
        error_msg = str(e)
        if "invalid_grant" in error_msg.lower():
            return GoogleVerifyResponse(
                success=False,
                message="Invalid credentials. Please check the service account JSON file."
            )
        elif "access_denied" in error_msg.lower() or "403" in error_msg:
            return GoogleVerifyResponse(
                success=False,
                message="Access denied. Please enable the required APIs in Google Cloud Console."
            )
        return GoogleVerifyResponse(
            success=False,
            message=f"Authentication failed: {error_msg}"
        )


@router.get("/supported-extensions")
async def get_supported_extensions():
    """Get list of all supported file extensions for extraction.

    Returns a flat list of all file extensions supported by all extractors.
    Empty string ("") indicates support for files without extensions.
    """
    from filevyasa.extractor import (
        ArchiveExtractor,
        CodeExtractor,
        GoogleDocsExtractor,
        ImageExtractor,
        MediaExtractor,
        NotebookExtractor,
        OfficeExtractor,
        PDFExtractor,
        TextExtractor,
        UnhandledExtractor,
        WebContentExtractor,
    )

    # Collect all extensions from all extractors
    all_extensions = set()

    extractors = [
        TextExtractor,
        PDFExtractor,
        OfficeExtractor,
        NotebookExtractor,
        WebContentExtractor,
        ImageExtractor,
        MediaExtractor,
        CodeExtractor,
        ArchiveExtractor,
        GoogleDocsExtractor,
        UnhandledExtractor,
    ]

    for extractor in extractors:
        all_extensions.update(extractor.supported_extensions())

    # Add empty string to indicate support for files without extensions
    all_extensions.add("")

    return sorted(all_extensions)


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
