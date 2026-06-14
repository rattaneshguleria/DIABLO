"""Voice assistant support for Diablo.

This module provides optional speech recognition and text-to-speech.
"""

from __future__ import annotations

import logging
import tempfile
import wave
from pathlib import Path

from config import Settings
from core.exceptions import DiabloError

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    import pyttsx3
except ImportError:  # pragma: no cover
    pyttsx3 = None

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None

try:
    import whisper
except ImportError:  # pragma: no cover
    whisper = None

logger = logging.getLogger("diablo.system.voice")


class VoiceAssistant:
    """Wrap speech recognition and text-to-speech for Diablo."""

    def __init__(
        self,
        *,
        wake_words: tuple[str, ...] = ("hey diablo", "diablo"),
        speech_model: str = "small",
        wake_listen_duration: int = 4,
        command_listen_duration: int = 8,
        sample_rate: int = 16000,
    ) -> None:
        if pyttsx3 is None:
            raise DiabloError(
                "Voice output requires pyttsx3. Install the optional voice dependencies."
            )
        if sd is None:
            raise DiabloError(
                "Voice input requires sounddevice. Install the optional voice dependencies."
            )
        if whisper is None:
            raise DiabloError(
                "Speech recognition requires whisper. Install the optional voice dependencies."
            )
        if np is None:
            raise DiabloError(
                "Voice support requires numpy. Install the optional voice dependencies."
            )

        self.wake_words = tuple(word.lower() for word in wake_words if word)
        self.wake_listen_duration = wake_listen_duration
        self.command_listen_duration = command_listen_duration
        self.sample_rate = sample_rate
        self.engine = pyttsx3.init()
        self.model = whisper.load_model(speech_model)

    @classmethod
    def from_settings(cls, settings: Settings) -> "VoiceAssistant":
        return cls(
            wake_words=settings.voice_wake_words,
            speech_model=settings.voice_speech_model,
            wake_listen_duration=settings.voice_wakeword_duration_seconds,
            command_listen_duration=settings.voice_input_duration_seconds,
            sample_rate=settings.voice_sample_rate,
        )

    def speak(self, text: str) -> None:
        if not text:
            return
        logger.info("Speaking response (%d chars)", len(text))
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self, duration: int) -> str:
        self._ensure_audio_available()
        logger.info("Recording audio for %d seconds", duration)
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        audio_file = self._save_wav(recording)

        try:
            transcription = self._transcribe(audio_file)
            logger.info("Transcription result: %s", transcription)
            return transcription.strip()
        finally:
            try:
                audio_file.unlink(missing_ok=True)
            except OSError:
                logger.debug("Failed to delete temporary audio file %s", audio_file)

    def wait_for_wake_word(self) -> str:
        while True:
            phrase = self.listen(self.wake_listen_duration)
            normalized = phrase.lower()
            if any(word in normalized for word in self.wake_words):
                return phrase
            logger.debug("Wake word not detected in: %s", normalized)

    def listen_command(self) -> str:
        return self.listen(self.command_listen_duration)

    def _ensure_audio_available(self) -> None:
        if sd is None:
            raise DiabloError(
                "Cannot record audio because the sounddevice library is unavailable."
            )

    def _save_wav(self, audio: "np.ndarray") -> Path:
        if np is None:
            raise DiabloError("Cannot save audio without numpy.")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            path = Path(handle.name)

        audio = np.asarray(audio, dtype=np.int16)
        with wave.open(str(path), "wb") as wave_file:
            wave_file.setnchannels(1)
            wave_file.setsampwidth(2)
            wave_file.setframerate(self.sample_rate)
            wave_file.writeframes(audio.tobytes())

        return path

    def _transcribe(self, audio_path: Path) -> str:
        try:
            result = self.model.transcribe(str(audio_path))
            return str(result.get("text", "")).strip()
        except Exception as exc:
            raise DiabloError("Failed to transcribe audio", details=str(exc))
