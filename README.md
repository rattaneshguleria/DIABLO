# Diablo

**Diablo** is a personal AI operating system inspired by JARVIS.

**Current status: Phase 6 — Vision**

---

## What works now

- CLI chat with local Ollama LLM
- Persistent memory (SQLite + ChromaDB)
- Tool calling (calculator, files, web, commands)
- **Desktop control** — apps, screenshots, clipboard, volume, mouse, keyboard
- **Voice assistant** — wake words, speech recognition, and spoken responses
- **Vision** — describe images and screenshots, or answer questions about them
- Safety confirmations and audit logging
- 55+ unit tests

---

## Quick start

```bash
cd ~/Documents/diablo
source .venv/Scripts/activate
pip install -r requirements.txt
ollama pull llava
python main.py --check
python main.py
python main.py --voice
```

---

## Try these

```
Open Chrome
Launch VS Code
Take a screenshot
What's on my clipboard?
Set volume to 40
Create a folder called test_notes
List running applications
What's on my screen right now?
Describe the image at data/photo.png
```

---

## Documentation

- [Phase 3](docs/phase3.md) — Tool calling
- [Phase 4](docs/phase4.md) — Desktop control
- [Phase 5](docs/phase5.md) — Voice assistant
- [Phase 6](docs/phase6.md) — Vision

---

## Next phase

**Phase 7: Autonomous Planning** — multi-step task planning, self-correction, and longer-running agentic workflows that chain tools together without a human prompting each step.
