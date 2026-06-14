"""Tests for Diablo voice assistant support."""

import pytest

from core.exceptions import DiabloError
from config import Settings


def test_voice_settings_default() -> None:
    settings = Settings()
    assert settings.voice_enabled is False
    assert settings.voice_wake_words == ("hey diablo", "diablo")
    assert settings.voice_speech_model == "small"
    assert settings.voice_wakeword_duration_seconds == 4
    assert settings.voice_input_duration_seconds == 8


def test_voice_assistant_requires_optional_dependencies(monkeypatch) -> None:
    import system.voice as voice_module

    monkeypatch.setattr(voice_module, "pyttsx3", None)
    monkeypatch.setattr(voice_module, "sounddevice", None)
    monkeypatch.setattr(voice_module, "whisper", None)

    with pytest.raises(DiabloError, match="pyttsx3"):
        voice_module.VoiceAssistant.from_settings(Settings())
