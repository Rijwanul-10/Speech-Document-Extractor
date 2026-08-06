"""
Application Settings.

Centralized configuration management using Pydantic Settings.
All configuration is driven by environment variables, making it easy
to switch providers and adjust behavior without code changes.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Speech-Document-Extractor"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Provider Selection ---
    speech_provider: Literal["mock", "whisper"] = "mock"
    ocr_provider: Literal["mock", "paddleocr"] = "mock"

    # --- File Limits ---
    max_file_size_mb: int = 25

    # --- Whisper Settings ---
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # --- Supported File Types ---
    supported_audio_extensions: list[str] = [
        ".wav", ".mp3", ".flac", ".ogg", ".m4a", ".wma", ".aac", ".webm",
    ]
    supported_image_extensions: list[str] = [
        ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp",
    ]
    supported_document_extensions: list[str] = [".pdf"]

    @property
    def max_file_size_bytes(self) -> int:
        """Return the maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached singleton Settings instance.

    Uses lru_cache to ensure the settings are only loaded once
    from the environment / .env file.
    """
    return Settings()
