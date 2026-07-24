"""
Application configuration for Diablo.

Uses pydantic-settings to load values from environment variables and .env files.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Diablo."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Diablo"
    app_version: str = "0.7.0"
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

    # Memory (Phase 2)
    memory_enabled: bool = True
    sqlite_db_path: Path = Path("diablo.db")
    chroma_persist_dir: Path = Path("chroma")
    embedding_model: str = "nomic-embed-text"
    semantic_memory_enabled: bool = True
    memory_retrieval_top_k: int = 5
    auto_extract_memories: bool = True

    # Tools (Phase 3)
    tools_enabled: bool = True
    max_tool_steps: int = 5
    autonomous_planning_enabled: bool = True
    max_plan_steps: int = 8
    max_recovery_attempts: int = 2
    require_confirmation_for_commands: bool = True
    allowed_command_prefixes: str = "python,pip,git,dir,ls,echo,cd,type,pytest"
    web_search_enabled: bool = True
    tool_workspace_dir: Path | None = None
    max_file_read_bytes: int = 100_000
    command_timeout: int = 30

    # Desktop control (Phase 4)
    desktop_control_enabled: bool = True
    require_confirmation_for_desktop_input: bool = True
    screenshot_dir: Path = Path("screenshots")

    # Voice assistant (Phase 5)
    voice_enabled: bool = False
    voice_wake_words: tuple[str, ...] = ("hey diablo", "diablo")
    voice_speech_model: str = "small"
    voice_wakeword_duration_seconds: int = 4
    voice_input_duration_seconds: int = 8
    voice_sample_rate: int = 16000

    # Vision (Phase 6)
    vision_enabled: bool = True
    vision_model: str = "llava"
    vision_temperature: float = 0.4
    vision_max_tokens: int = 1024
    vision_max_image_dimension: int = 1024

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

    @field_validator("memory_retrieval_top_k")
    @classmethod
    def validate_top_k(cls, value: int) -> int:
        if value < 1:
            raise ValueError("memory_retrieval_top_k must be at least 1")
        return value

    @field_validator("max_tool_steps")
    @classmethod
    def validate_tool_steps(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_tool_steps must be at least 1")
        return value

    @field_validator("max_plan_steps")
    @classmethod
    def validate_plan_steps(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_plan_steps must be at least 1")
        return value

    @field_validator("max_recovery_attempts")
    @classmethod
    def validate_recovery_attempts(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_recovery_attempts cannot be negative")
        return value

    @field_validator(
        "voice_wakeword_duration_seconds",
        "voice_input_duration_seconds",
        "voice_sample_rate",
    )
    @classmethod
    def validate_voice_settings(cls, value: int) -> int:
        if value < 1:
            raise ValueError("voice audio duration and sample rate must be positive")
        return value

    @field_validator("vision_temperature")
    @classmethod
    def validate_vision_temperature(cls, value: float) -> float:
        if not 0.0 <= value <= 2.0:
            raise ValueError("vision_temperature must be between 0.0 and 2.0")
        return value

    @field_validator("vision_max_image_dimension")
    @classmethod
    def validate_vision_dimension(cls, value: int) -> int:
        if value < 64:
            raise ValueError("vision_max_image_dimension must be at least 64")
        return value

    def model_post_init(self, __context: object) -> None:
        if self.log_dir is None:
            self.log_dir = self.base_dir / "logs"
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
        if self.tool_workspace_dir is None:
            self.tool_workspace_dir = self.base_dir


def get_settings() -> Settings:
    """Return a settings instance."""
    return Settings()
