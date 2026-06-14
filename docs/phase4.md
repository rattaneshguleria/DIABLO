# Phase 4: Desktop Control

Phase 4 gives Diablo direct control over your Windows desktop — applications, files, screenshots, clipboard, volume, mouse, and keyboard.

---

## What Phase 4 Adds

| Tool | Risk | Description |
|------|------|-------------|
| `launch_application` | Medium | Open Chrome, VS Code, Spotify, Notepad, etc. |
| `close_application` | **High** | Close a running app (confirmation required) |
| `list_running_applications` | Low | List process names |
| `create_folder` | Low | Create directories |
| `move_file` | Medium | Move files/folders |
| `rename_file` | Medium | Rename files/folders |
| `take_screenshot` | Low | Save screen capture to `data/screenshots/` |
| `read_clipboard` | Medium | Read clipboard text |
| `get_volume` | Low | Current volume % |
| `set_volume` | Medium | Set volume 0–100% |
| `mouse_click` | **High** | Click at screen coordinates (confirmation) |
| `type_text` | **High** | Type text at cursor (confirmation) |
| `press_hotkey` | **High** | Press shortcuts like `ctrl,c` (confirmation) |

---

## Installation

```bash
cd ~/Documents/diablo
source .venv/Scripts/activate
pip install -r requirements.txt
```

New packages: `pyautogui`, `pywin32`, `pycaw`, `Pillow`

---

## Configuration (`.env`)

```env
DESKTOP_CONTROL_ENABLED=true
REQUIRE_CONFIRMATION_FOR_DESKTOP_INPUT=true
SCREENSHOT_DIR=screenshots
```

---

## Usage Examples

```
You: Open Chrome
You: Launch VS Code
You: Open Spotify
You: Take a screenshot
You: What's on my clipboard?
You: Set volume to 50
You: Create a folder called notes in my project
You: List running applications
```

High-risk actions prompt for confirmation:

```
Diablo wants to run 'mouse_click' with arguments: x=100, y=200. Allow? [y/N]:
```

---

## Safety

| Protection | Details |
|------------|---------|
| Confirmation | Mouse, keyboard, and close-app require **y/yes** |
| PyAutoGUI failsafe | Move mouse to top-left corner to abort |
| Blocked hotkeys | `win`, `delete`, etc. are blocked |
| System paths | File tools cannot access `System32`, `Windows`, etc. |
| Audit log | All actions logged to `logs/tool_audit.jsonl` |

---

## Options

```bash
python main.py --no-desktop    # Disable desktop tools only
python main.py --no-tools      # Disable all tools
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| App not found | Use full path or install the app (Chrome, VS Code, Spotify) |
| Volume control fails | `pip install pycaw` and restart |
| Clipboard fails | `pip install pywin32` |
| Screenshot fails | `pip install pyautogui Pillow` |
| Mouse/keyboard blocked | Type `y` when confirmation prompt appears |

---

## Next Phase

**Phase 5: Voice Assistant** — Whisper speech-to-text, Piper/pyttsx3 text-to-speech, wake words.
