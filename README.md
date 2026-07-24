# 🔥 DIABLO — AI Voice Assistant

<div align="center">



# 🔥 DIABLO

### Your Personal AI Voice Assistant

*"Talk naturally. Let DIABLO handle the rest."*

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)
![Whisper](https://img.shields.io/badge/OpenAI-Whisper-black?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?style=for-the-badge&logo=google)
![AI](https://img.shields.io/badge/AI-Voice%20Assistant-red?style=for-the-badge)

</div>

---

# 📖 Overview

DIABLO is a desktop AI voice assistant that listens to spoken commands, converts speech to text, reasons with a large language model, and responds naturally using text-to-speech. It is designed as a modular assistant that can be extended with automation, desktop control, and custom skills.

---

# ✨ Features

- 🎙️ Speech-to-Text (Whisper)
- 🤖 AI-powered conversations
- 🔊 Text-to-Speech responses
- 🖥️ Desktop automation ready
- ⚡ Modular Python architecture
- 🔌 Easy integration with LLM providers
- 🧩 Extensible command system

---

# 🏗️ Architecture

```mermaid
flowchart LR
A[🎤 Microphone] --> B[Whisper STT]
B --> C[Command Processor]
C --> D[LLM]
D --> E[Response Generator]
E --> F[pyttsx3 TTS]
F --> G[🔊 Speaker]
```

---

# 🚀 Workflow

1. Capture voice.
2. Convert speech to text.
3. Process command.
4. Generate AI response.
5. Speak the response.
6. Wait for the next command.

---

# 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python |
| STT | Whisper |
| TTS | pyttsx3 |
| Audio | sounddevice |
| AI | Gemini / Compatible LLM |
| Environment | VS Code |

---

# 📂 Suggested Structure

```text
DIABLO/
├── assets/
│   ├── banner.png
│   ├── diablo-avatar.png
│   └── demo.gif
├── voice.py
├── assistant.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 📸 README Assets

Place these files inside `assets/`:

- banner.png
- diablo-avatar.png
- demo.gif
- architecture.png
- workflow.png

---

# 🧠 Future Roadmap

- Wake word activation
- Smart home control
- Browser automation
- Calendar integration
- Email assistant
- Local knowledge base
- Vision support
- Autonomous multi-step planning with recovery
- Plugin system

---

# 🤝 Contributing

Fork → Branch → Commit → Pull Request.

---

# 📜 License

MIT License.

---

# 👨‍💻 Developer

**Rattanesh Guleria**  
B.Tech Computer Science Engineering  
Lovely Professional University

GitHub: https://github.com/rattaneshguleria

---

# 🎨 Branding Notes

- Use a dark cyberpunk theme.
- Use the provided avatar as `assets/diablo-avatar.png`.
- Create a matching banner with purple/black gradients and glowing red accents.
- Add screenshots and a demo GIF for the best presentation.

<div align="center">

## ⭐ Star the repository if you like the project!

</div>
