# Phase 5: Voice Assistant

Phase 5 gives Diablo a voice: wake words, speech recognition, and spoken responses.

---

## What Phase 5 Adds

| Feature | Risk | Description |
|---------|------|-------------|
| `voice_mode` | Medium | Run Diablo as a voice assistant from the terminal |
| Wake words | Low | Listen for "Hey Diablo" or "Diablo" to begin a command |
| Speech recognition | Medium | Convert microphone audio to text with Whisper |
| Text-to-speech | Low | Speak Diablo's response using pyttsx3 |

---

## Installation

Make sure the optional voice dependencies are installed:

```bash
pip install -r requirements.txt
```

If you want a smaller install and already have `pyttsx3`, `sounddevice`, and `openai-whisper`, you can skip the full voice dependency set.

---

## Usage

Run Diablo in voice assistant mode:

```bash
python main.py --voice
```

Say "Hey Diablo" or "Diablo" to wake the assistant, then speak your request.

You can say:

- "Open Chrome"
- "What is the weather today?"
- "Read my clipboard"
- "Quit"

Voice mode still uses the same Ollama model, memory, and tool support as the normal CLI.

---

## Notes

- Voice mode uses local speech recognition and does not require an internet-based STT provider.
- If audio dependencies are missing, Diablo will report the missing packages and suggest installation.
- The assistant does not yet have vision.
