"""Tests for configuration."""

import pytest

from config import Settings, get_settings


def test_default_settings() -> None:
    settings = Settings()
    assert settings.app_name == "Diablo"
    assert settings.ollama_host == "http://localhost:11434"
    assert settings.log_dir.name == "logs"
    assert settings.data_dir.name == "data"
    assert settings.memory_enabled is True
    assert settings.embedding_model == "nomic-embed-text"
    assert settings.sqlite_db_path.name == "diablo.db"
    assert settings.voice_enabled is False
    assert settings.voice_wake_words == ("hey diablo", "diablo")
    assert settings.voice_speech_model == "small"


def test_invalid_log_level() -> None:
    with pytest.raises(ValueError, match="log_level"):
        Settings(log_level="VERBOSE")


def test_invalid_temperature() -> None:
    with pytest.raises(ValueError, match="ollama_temperature"):
        Settings(ollama_temperature=3.0)


def test_get_settings_returns_instance() -> None:
    settings = get_settings()
    assert isinstance(settings, Settings)
