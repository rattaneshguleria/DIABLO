# Phase 3: Tool Calling

Phase 3 gives Diablo the ability to use tools — executing real actions like calculations, file reads, web searches, and safe shell commands.

---

## What Phase 3 Adds

| Capability | Description |
|------------|-------------|
| Tool registry | Central catalog of available tools |
| Tool executor | Runs tools with safety checks and audit logs |
| Tool loop | LLM can request tools, observe results, and respond |
| Built-in tools | Calculator, files, system info, web search, commands |
| CLI integration | `/tools` command, confirmation prompts, activity display |

---

## Architecture

```
User message
    │
    ▼
DiabloAgent
    │
    ├── Build prompt + memory context
    ├── Send to Ollama with tool schemas
    │
    ├── LLM requests tool call?
    │       YES → ToolExecutor runs tool → result back to LLM → repeat
    │       NO  → Final answer to user
    │
    └── Save exchange to memory
```

---

## Built-in Tools

| Tool | Risk | Description |
|------|------|-------------|
| `calculator` | Low | Safe math evaluation |
| `get_current_time` | Low | Current date/time |
| `read_file` | Medium | Read a text file |
| `write_file` | Medium | Write a text file |
| `list_directory` | Low | List folder contents |
| `search_files` | Low | Find files by pattern |
| `get_system_info` | Low | CPU, memory, disk info |
| `web_search` | Medium | DuckDuckGo search |
| `fetch_url` | Medium | Read webpage text |
| `run_command` | **High** | Shell commands (requires confirmation) |

---

## Installation

### 1. Install dependencies

```bash
cd ~/Documents/diablo
source .venv/Scripts/activate
pip install -r requirements.txt
```

### 2. Update `.env`

Add the Phase 3 settings from `.env.example`:

```env
TOOLS_ENABLED=true
MAX_TOOL_STEPS=5
REQUIRE_CONFIRMATION_FOR_COMMANDS=true
ALLOWED_COMMAND_PREFIXES=python,pip,git,dir,ls,echo,cd,type,pytest
WEB_SEARCH_ENABLED=true
```

### 3. Health check

```bash
python main.py --check
```

You should see registered tools listed.

---

## Usage Examples

```
You: What is 15% of 240?
You: What time is it?
You: List files in this project
You: Read README.md
You: Search the web for Python 3.12 features
You: What's my CPU usage?
```

For shell commands, Diablo will ask for confirmation:

```
Diablo wants to run 'run_command' with arguments: command='echo hello'. Allow? [y/N]:
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `/tools` | List all available tools |
| `/help` | Show all commands |

---

## Options

```bash
python main.py --no-tools    # Disable tools for this session
```

---

## Security

- System directories are blocked for file tools
- `run_command` requires user confirmation
- Only allowed command prefixes can run
- Dangerous commands (`del`, `format`, `shutdown`, etc.) are blocked
- All tool executions are logged to `logs/tool_audit.jsonl`

---

## Testing

```bash
pytest -v
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Model doesn't call tools | Use a tool-capable model (llama3.2+). Some models handle tools better than others |
| Web search fails | Check internet connection; set `WEB_SEARCH_ENABLED=false` to disable |
| Command denied | Add prefix to `ALLOWED_COMMAND_PREFIXES` in `.env` |
| File access blocked | Use paths inside the project workspace |

---

## Next Phase

**Phase 4: Desktop Control** — mouse, keyboard, app launching, volume, screenshots.
