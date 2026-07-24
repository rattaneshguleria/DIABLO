# Phase 7: Autonomous Planning

Phase 7 lets Diablo carry out bounded multi-step tasks with progress-aware recovery. The planner uses the existing LLM tool-calling contract, so every action still passes through the normal validation, confirmation, and audit path.

## What Phase 7 Adds

| Capability | Description |
|------------|-------------|
| Task planning | Break a request into sequential tool steps and inspect each result |
| Self-correction | Give failed tool results back to the model so it can correct arguments or choose another tool |
| Bounded execution | Stop after a configurable number of plan steps or recovery attempts |
| Progress events | Report tool `running`, `done`, `failed`, and plan `recovering` states to the CLI or another UI |

## Configuration (`.env`)

```env
AUTONOMOUS_PLANNING_ENABLED=true
MAX_PLAN_STEPS=8
MAX_RECOVERY_ATTEMPTS=2
```

`MAX_PLAN_STEPS` limits the number of model/tool rounds. `MAX_RECOVERY_ATTEMPTS` limits how many rounds may contain failed tools before Diablo stops and explains that it could not complete the task.

## Usage Examples

```
You: Find the latest screenshot, describe it, and tell me whether it contains an error.
You: Create a notes folder, write a summary file, and verify that it exists.
You: Check the current volume and lower it if it is above 80 percent.
```

Diablo can now inspect the output from one step before selecting the next step. A failed action is not silently treated as success; the failure is returned to the model and recorded in the audit log.

## Safety

- All actions continue to use `ToolExecutor`.
- High-risk tools still require confirmation for every attempted call.
- Plan limits prevent unbounded loops.
- Failed and recovered tool calls remain visible in activity callbacks and audit history.

## Options

```bash
# Disable autonomous planning while retaining the legacy bounded tool loop
# in .env:
AUTONOMOUS_PLANNING_ENABLED=false
```

## Next Phase

Phase 8 can add scheduled tasks and resumable plans backed by persistent storage.
