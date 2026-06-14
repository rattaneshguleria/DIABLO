# Phase 2: Memory System

Phase 2 adds persistent memory to Diablo so it can remember facts, preferences, and relevant past context across sessions.

---

## What Phase 2 Adds

| Capability | Storage | Description |
|------------|---------|-------------|
| Short-term memory | RAM | Current session conversation buffer |
| Long-term memory | SQLite | Structured facts and preferences |
| Episodic memory | SQLite | Conversation sessions and message timeline |
| Semantic memory | ChromaDB | Meaning-based retrieval via embeddings |
| Auto-extraction | Heuristics | Detects phrases like "My name is..." |
| CLI memory commands | — | `/remember`, `/memories`, `/forget`, `/sessions` |

---

## Architecture

```
User message
    │
    ▼
DiabloAgent
    │
    ├── MemoryManager.retrieve_context()
    │       ├── LongTermMemory (facts, preferences)
    │       └── SemanticMemory (vector search)
    │
    ├── Inject memory context into LLM prompt
    │
    ├── Ollama LLM response
    │
    └── MemoryManager.store_exchange()
            ├── EpisodicMemory (SQLite)
            ├── SemanticMemory (ChromaDB)
            └── Auto-extract structured memories
```

---

## New Files

| File | Purpose |
|------|---------|
| `memory/models.py` | Dataclasses for memories, sessions, context |
| `memory/short_term.py` | In-session message buffer |
| `memory/long_term.py` | SQLite facts and preferences |
| `memory/episodic.py` | Conversation session timeline |
| `memory/semantic.py` | ChromaDB vector store |
| `memory/embeddings.py` | Ollama embedding client |
| `memory/extractor.py` | Auto memory extraction heuristics |
| `memory/manager.py` | Central memory orchestrator |
| `database/connection.py` | SQLite connection wrapper |
| `database/migrations.py` | Schema initialization |

---

## Installation

### 1. Install new dependencies

```bash
cd ~/Documents/diablo
source .venv/Scripts/activate
pip install -r requirements.txt
```

### 2. Pull the embedding model

Semantic memory uses a local Ollama embedding model:

```bash
"/c/Users/ACER/AppData/Local/Programs/Ollama/ollama.exe" pull nomic-embed-text
```

### 3. Update `.env`

Copy new settings from `.env.example` if needed:

```env
MEMORY_ENABLED=true
SQLITE_DB_PATH=diablo.db
CHROMA_PERSIST_DIR=chroma
EMBEDDING_MODEL=nomic-embed-text
SEMANTIC_MEMORY_ENABLED=true
MEMORY_RETRIEVAL_TOP_K=5
AUTO_EXTRACT_MEMORIES=true
```

### 4. Run health check

```bash
python main.py --check
```

---

## Usage

### Natural memory

Diablo auto-detects statements like:

- `My name is Alex`
- `I prefer Python`
- `Remember that my project is called Diablo`

### CLI commands

| Command | Description |
|---------|-------------|
| `/remember <fact>` | Explicitly store a memory |
| `/memories` | List all stored memories |
| `/forget <key>` | Remove a memory by key |
| `/sessions` | List recent conversation sessions |
| `/clear` | Clear current session (persistent memory remains) |

### Disable memory for one run

```bash
python main.py --no-memory
```

---

## Testing

```bash
pytest -v
```

Tests use temporary databases and fake embeddings — Ollama is not required for unit tests.

---

## Data locations

| Path | Contents |
|------|----------|
| `data/diablo.db` | SQLite: sessions, messages, structured memories |
| `data/chroma/` | ChromaDB vector index |

Both directories are gitignored.

---

## Security

- Sensitive keywords (`password`, `secret`, `token`, etc.) are not auto-stored
- `/forget` requires an explicit key
- Memory files stay local on your machine

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Embedding model error | Run `ollama pull nomic-embed-text` |
| Semantic memory disabled | Set `SEMANTIC_MEMORY_ENABLED=false` to use SQLite-only memory |
| ChromaDB import error | Run `pip install chromadb` |
| Memory not recalled | Use `/memories` to verify storage; try `/remember` explicitly |

---

## Next Phase

**Phase 3: Tool Calling** — Diablo will gain the ability to call tools (file operations, web search, calculations, etc.).
