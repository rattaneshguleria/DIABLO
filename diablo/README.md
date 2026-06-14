# Diablo

**Diablo** is a personal AI operating system inspired by JARVIS — a modular, local-first assistant for conversation, reasoning, planning, memory, tools, and autonomous execution.

This repository is built **incrementally in phases**. Phase 1 delivers a production-quality CLI chatbot powered by [Ollama](https://ollama.com).

---

## Phase 1: Basic Chatbot (Ollama)

### What works now

- Interactive CLI conversation
- Local LLM inference via Ollama
- Diablo personality (system prompt)
- In-session conversation history
- Streaming responses
- Structured logging
- Configuration via `.env`
- Unit tests with mocks

### What comes later

- Phase 2: Persistent memory (ChromaDB, SQLite/PostgreSQL)
- Phase 3: Tool calling
- Phase 4+: Desktop control, voice, vision, multi-agent system, and more

---

## Requirements

- **Python 3.12+**
- **Ollama** installed and running on Windows
- At least one Ollama model pulled (e.g. `llama3.2`, `qwen3`, `llama3.3`, `deepseek-r1`)

---

## Installation

### 1. Install Ollama

Download and install from [https://ollama.com/download](https://ollama.com/download).

Verify Ollama is running:

```bash
ollama --version
```

### 2. Pull a model

```bash
ollama pull llama3.2
```

Supported models for future phases include Qwen3, Llama 3.3, and DeepSeek — any Ollama-compatible model works in Phase 1.

### 3. Set up Python environment

```bash
cd diablo
python -m venv .venv

# Windows (Git Bash / PowerShell)
source .venv/Scripts/activate   # Git Bash
# .venv\Scripts\activate        # PowerShell / CMD

pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` if needed:

```env
OLLAMA_MODEL=llama3.2
OLLAMA_HOST=http://localhost:11434
STREAM_RESPONSES=true
```

---

## Usage

### Health check

```bash
python main.py --check
```

### Start Diablo

```bash
python main.py
```

### CLI commands

| Command  | Description                    |
|----------|--------------------------------|
| `/help`  | Show help                      |
| `/clear` | Clear conversation history   |
| `/exit`  | Exit Diablo                    |

### Disable streaming

```bash
python main.py --no-stream
```

---

## Project structure (Phase 1)

```
diablo/
├── main.py              # Application entry point
├── config.py            # Settings and environment variables
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── agents/
│   └── diablo_agent.py  # Core conversational agent
├── llm/
│   ├── base.py          # LLM interface (abstract)
│   └── ollama_client.py # Ollama implementation
├── core/
│   ├── exceptions.py    # Custom exceptions
│   └── logging_config.py
├── ui/
│   └── cli.py           # Terminal interface
├── memory/              # Reserved for Phase 2
├── tools/               # Reserved for Phase 3
├── logs/                # Rotating log files
├── data/                # Future persistent data
├── tests/               # Unit tests
└── docs/
    └── phase1.md
```

---

## Testing

```bash
pytest -v
```

Tests mock Ollama — you do not need Ollama running for unit tests.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Ollama is not reachable` | Start Ollama app or run `ollama serve` |
| `Model 'x' is not installed` | Run `ollama pull <model>` |
| Import errors | Run commands from the `diablo/` project root |
| Empty responses | Try another model or increase `OLLAMA_MAX_TOKENS` |

---

## License

Personal project — use and extend as you build your JARVIS.
