# Phase 6: Vision

Phase 6 gives Diablo eyes — it can look at an image file or take a screenshot and describe what it sees, using a local multimodal model through Ollama.

---

## What Phase 6 Adds

| Tool | Risk | Description |
|------|------|-------------|
| `describe_image` | Low | Look at an image file on disk and describe it, or answer a question about it |
| `describe_screen` | Low | Take a screenshot and describe what's currently on screen, or answer a question about it |

---

## Installation

No new Python packages are required — Phase 6 reuses `ollama` (already installed) and `Pillow` (already installed for screenshots).

You do need a **multimodal (vision-capable) model** pulled in Ollama:

```bash
ollama pull llava
```

Other options if you want to try alternatives:

```bash
ollama pull llama3.2-vision   # larger, more capable, needs more RAM/VRAM
ollama pull moondream         # smaller and faster, lower quality
ollama pull bakllava
```

`llava` is the default and a good balance of speed and quality for most machines.

---

## Configuration (`.env`)

```env
VISION_ENABLED=true
VISION_MODEL=llava
VISION_TEMPERATURE=0.4
VISION_MAX_TOKENS=1024
VISION_MAX_IMAGE_DIMENSION=1024
```

- `VISION_MODEL` must match a model you've pulled with `ollama pull`.
- `VISION_MAX_IMAGE_DIMENSION` controls how large images are resized to before sending them to the model (smaller = faster, less detail).
- Vision uses its own model setting, independent of `OLLAMA_MODEL` (your main chat model can stay text-only).

---

## Usage Examples

```
You: What's on my screen right now?
You: Describe my screen
You: Is there an error message visible on screen?
You: Describe the image at C:\Users\you\Pictures\photo.jpg
You: What's in screenshots/screenshot_20260617_101500.png?
You: Does this image contain a person? data/photo.png
```

Diablo will call `describe_screen` or `describe_image`, run it through the vision model, and answer in natural language — same as any other tool call.

---

## How It Works

1. `describe_image` / `describe_screen` resolve the target image (an existing file, or a fresh screenshot via the same `take_screenshot` helper Phase 4 uses).
2. `system/image.py` opens the image with Pillow, resizes it if it's larger than `VISION_MAX_IMAGE_DIMENSION`, and base64-encodes it as JPEG.
3. `llm/vision.py` sends the image + prompt to your configured `VISION_MODEL` via Ollama's multimodal chat API — a separate client from your main text chat model.
4. The text description comes back as a normal tool result and gets folded into Diablo's response, same as any other tool.

Vision does not give Diablo a live video feed or screen-watching loop yet — each call is a single snapshot, requested on demand.

---

## Safety

| Protection | Details |
|------------|---------|
| Read-only | Vision tools only read images; they cannot modify files or the screen |
| Risk level | Both tools are Low risk — no confirmation prompt required |
| Size limits | Images are resized before sending, capping memory/compute use |
| Audit log | Calls are logged to `logs/tool_audit.jsonl` like any other tool |

---

## Options

```bash
# Disable vision tools entirely
# in .env:
VISION_ENABLED=false
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Vision model 'llava' not found" | Run `ollama pull llava` |
| "Cannot connect to Ollama" | Make sure Ollama is running (`ollama serve` or the desktop app) |
| Slow responses | Lower `VISION_MAX_IMAGE_DIMENSION`, or try `moondream` for speed |
| Inaccurate descriptions | Try a larger model like `llama3.2-vision`, or ask a more specific question |
| "Unsupported image type" | Convert the image to png/jpg/jpeg/webp/bmp/gif first |

---

## Next Phase

**Phase 7: Autonomous Planning** — multi-step task planning, self-correction, and longer-running agentic workflows that chain tools (including vision) together without a human prompting each step.
