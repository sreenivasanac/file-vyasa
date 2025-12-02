"""Application configuration settings."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_config_path() -> Path | None:
    """Get the path to the settings.yaml file."""
    config_paths = [
        Path(__file__).parent.parent / "config" / "settings.yaml",
        Path("config/settings.yaml"),
    ]
    for config_path in config_paths:
        if config_path.exists():
            return config_path
    return None


def load_yaml_config() -> dict:
    """Load configuration from YAML file."""
    config_path = get_config_path()
    if config_path:
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def save_yaml_config(config: dict) -> bool:
    """Save configuration to YAML file. Returns True on success."""
    config_path = get_config_path()
    if not config_path:
        return False
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    return True


def update_yaml_setting(section: str, key: str, value) -> bool:
    """Update a specific setting in the YAML file and save it."""
    config = load_yaml_config()
    if section not in config:
        config[section] = {}
    config[section][key] = value
    return save_yaml_config(config)


# Load YAML config once at module import
_yaml_config = load_yaml_config()


class Settings(BaseSettings):
    """
    Application settings.

    Priority (highest to lowest):
    1. Environment variables (FILEVYASA_* prefix)
    2. .env file
    3. config/settings.yaml
    4. Default values
    """

    model_config = SettingsConfigDict(
        env_prefix="FILEVYASA_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # App settings
    app_name: str = _yaml_config.get("app", {}).get("name", "FileVyasa")
    debug: bool = _yaml_config.get("app", {}).get("debug", False)

    # API settings
    api_host: str = _yaml_config.get("api", {}).get("host", "127.0.0.1")
    api_port: int = _yaml_config.get("api", {}).get("port", 8000)

    # Database settings
    db_path: Path = Field(
        default=Path(_yaml_config.get("database", {}).get("path", ".filevyasa/app.db")),
        description="Path to SQLite database file"
    )

    # LLM settings (BYOK)
    llm_provider: str = Field(
        default=_yaml_config.get("llm", {}).get("provider", "openai"),
        description="LLM provider: openai, anthropic, etc."
    )
    llm_model: str = Field(
        default=_yaml_config.get("llm", {}).get("model", "gpt-4o-mini"),
        description="Model name for summarization"
    )
    llm_api_key: Optional[str] = Field(default=None, description="API key for LLM provider")
    llm_api_base: Optional[str] = Field(
        default=_yaml_config.get("llm", {}).get("api_base"),
        description="Custom API base URL"
    )

    # Extraction settings
    max_content_lines: int = Field(
        default=_yaml_config.get("extraction", {}).get("max_content_lines", 50),
        description="Max lines to read for summarization"
    )

    # Google Workspace API settings
    google_credentials_path: Optional[str] = Field(
        default=_yaml_config.get("google", {}).get("credentials_path"),
        description="Path to Google service account credentials JSON file"
    )

    # Scan settings
    default_ignore_patterns: list[str] = Field(
        default=_yaml_config.get("scan", {}).get("default_ignore_patterns", [
            ".git",
            ".svn",
            "__pycache__",
            "node_modules",
            ".DS_Store",
            "*.pyc",
            ".venv",
            "venv",
        ]),
        description="Default patterns to ignore during scan"
    )

    # Sync parallel processing settings
    sync_extraction_workers: int = Field(
        default=_yaml_config.get("sync", {}).get("extraction_workers", 8),
        description="Number of parallel workers for content extraction"
    )
    sync_ai_workers: int = Field(
        default=_yaml_config.get("sync", {}).get("ai_workers", 4),
        description="Number of parallel workers for AI processing"
    )
    sync_db_batch_size: int = Field(
        default=_yaml_config.get("sync", {}).get("db_batch_size", 10),
        description="Batch size for database operations (smaller = more responsive UI)"
    )
    sync_enable_parallel: bool = Field(
        default=_yaml_config.get("sync", {}).get("enable_parallel", True),
        description="Enable parallel processing during sync"
    )


# Global settings instance
settings = Settings()


def get_db_path() -> Path:
    """Get the absolute path to the database, creating parent dirs if needed."""
    db_path = settings.db_path
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path
