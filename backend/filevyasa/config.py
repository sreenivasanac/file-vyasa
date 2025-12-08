"""Application configuration settings."""

import json
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_local_config_path() -> Path:
    """Get the path to the local_config.json file in .filevyasa directory."""
    return Path.cwd() / ".filevyasa" / "local_config.json"


def load_local_config() -> dict:
    """Load configuration from local_config.json file."""
    config_path = get_local_config_path()
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f) or {}
    return {}


def save_local_config(config: dict) -> bool:
    """Save configuration to local_config.json file. Returns True on success."""
    config_path = get_local_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return True


def update_local_config_setting(key: str, value) -> bool:
    """Update a specific setting in the local_config.json file and save it."""
    config = load_local_config()
    config[key] = value
    return save_local_config(config)


def get_local_config_setting(key: str, default=None):
    """Get a specific setting from local_config.json."""
    config = load_local_config()
    return config.get(key, default)


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

# Load local config once at module import
_local_config = load_local_config()


class Settings(BaseSettings):
    """
    Application settings.

    Priority (highest to lowest):
    1. Environment variables (FILEVYASA_* prefix)
    2. .env file
    3. .filevyasa/local_config.json (user-specific settings)
    4. config/settings.yaml
    5. Default values
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
    # Priority: env var > local_config.json > settings.yaml
    google_credentials_path: Optional[str] = Field(
        default=_local_config.get("google_credentials_path")
        or _yaml_config.get("google", {}).get("credentials_path"),
        description="Path to Google service account credentials JSON file"
    )

    # Scan settings - file patterns to skip (glob patterns matched against filename)
    ignore_file_patterns: list[str] = Field(
        default=_yaml_config.get("scan", {}).get("ignore_file_patterns", [
            # macOS system files
            ".DS_Store",
            ".AppleDouble",
            ".LSOverride",
            # Windows system files
            "Thumbs.db",
            "ehthumbs.db",
            "desktop.ini",
            # Linux system files
            ".directory",
            # Development artifacts
            "*.pyc",
            "*.pyo",
        ]),
        description="File patterns to skip (glob patterns)"
    )

    # Scan settings - folder names to skip entirely (not traversed into)
    ignore_folder_names: list[str] = Field(
        default=_yaml_config.get("scan", {}).get("ignore_folder_names", [
            # macOS system folders
            ".Spotlight-V100",
            ".Trashes",
            ".fseventsd",
            # Version control
            ".git",
            ".svn",
            ".hg",
            # Package managers / dependencies
            "node_modules",
            "bower_components",
            # Python environments
            "__pycache__",
            ".venv",
            "venv",
            ".tox",
            ".nox",
            ".pytest_cache",
            ".mypy_cache",
        ]),
        description="Folder names to skip entirely (not traversed)"
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
        default=_yaml_config.get("sync", {}).get("db_batch_size", 1),
        description="Batch size for DB operations (1 = per-file updates, more responsive UI)"
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
