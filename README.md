# Diablo

**Diablo** is a personal AI operating system inspired by JARVIS.

**Current status: Phase 5 — Voice Assistant**

---

## What works now

- CLI chat with local Ollama LLM
- Persistent memory (SQLite + ChromaDB)
- Tool calling (calculator, files, web, commands)
- **Desktop control** — apps, screenshots, clipboard, volume, mouse, keyboard
- **Voice assistant** — wake words, speech recognition, and spoken responses
- Safety confirmations and audit logging
- 55+ unit tests

---

## Quick start

```bash
cd ~/Documents/diablo
source .venv/Scripts/activate
pip install -r requirements.txt
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
```

---

## Documentation

- [Phase 3](docs/phase3.md) — Tool calling
- [Phase 4](docs/phase4.md) — Desktop control
- [Phase 5](docs/phase5.md) — Voice assistant

---

## Next phase

**Phase 6: Vision** — image understanding, screen analysis, and computer vision.
