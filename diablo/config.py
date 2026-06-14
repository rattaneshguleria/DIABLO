"""
Application configuration for Diablo.

Uses pydantic-settings to load values from environment variables and .env files.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Diablo Phase 1."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Diablo"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    log_to_file: bool = True

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent)
    log_dir: Path | None = None
    data_dir: Path | None = None

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout: int = 120
    ollama_temperature: float = 0.7
    ollama_max_tokens: int = 2048

    # Chat behavior
    stream_responses: bool = True
    max_history_messages: int = 20

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}")
        return upper

    @field_validator("ollama_temperature")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        if not 0.0 <= value <= 2.0:
            raise ValueError("ollama_temperature must be between 0.0 and 2.0")
        return value

    def model_post_init(self, __context: object) -> None:
        if self.log_dir is None:
            self.log_dir = self.base_dir / "logs"
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"


def get_settings() -> Settings:
    """Return a cached-friendly settings instance."""
    return Settings()
