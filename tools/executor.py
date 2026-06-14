"""Tool execution with safety checks and audit logging."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from core.exceptions import ToolExecutionError, ToolNotFoundError
from tools.base import ConfirmationCallback, ToolAuditEntry, ToolCall, ToolResult
from tools.registry import ToolRegistry
from tools.safety import default_confirmation_message

logger = logging.getLogger("diablo.tools.executor")


class ToolExecutor:
    """Execute tools with confirmation, validation, and audit trails."""

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        audit_log_path: Path | None = None,
        require_confirmation_for_high_risk: bool = True,
        confirm_callback: ConfirmationCallback | None = None,
    ) -> None:
        self.registry = registry
        self.audit_log_path = audit_log_path
        self.require_confirmation_for_high_risk = require_confirmation_for_high_risk
        self.confirm_callback = confirm_callback
        self.audit_history: list[ToolAuditEntry] = []

        if self.audit_log_path is not None:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def execute(self, call: ToolCall) -> ToolResult:
        """Execute a single tool call."""
        try:
            tool = self.registry.get(call.name)
        except ToolNotFoundError as exc:
            result = ToolResult(
                success=False,
                output="",
                error=str(exc),
                tool_name=call.name,
            )
            self._audit(call, result)
            return result

        if tool.requires_confirmation() and self.require_confirmation_for_high_risk:
            if not self._request_confirmation(call):
                result = ToolResult(
                    success=False,
                    output="",
                    error="User denied tool execution",
                    tool_name=call.name,
                )
                self._audit(call, result)
                return result

        try:
            result = tool.run(**call.arguments)
            result.tool_name = call.name
        except ToolExecutionError as exc:
            result = ToolResult(
                success=False,
                output="",
                error=str(exc),
                tool_name=call.name,
            )
        except Exception as exc:  # noqa: BLE001 - tool boundary guard
            logger.exception("Tool '%s' failed", call.name)
            result = ToolResult(
                success=False,
                output="",
                error=f"Unexpected error: {exc}",
                tool_name=call.name,
            )

        self._audit(call, result)
        return result

    def _request_confirmation(self, call: ToolCall) -> bool:
        message = default_confirmation_message(call.name, call.arguments)
        if self.confirm_callback is None:
            logger.warning("Confirmation required but no callback configured; denying tool")
            return False
        return self.confirm_callback(message)

    def _audit(self, call: ToolCall, result: ToolResult) -> None:
        entry = ToolAuditEntry(
            tool_name=call.name,
            arguments=call.arguments,
            success=result.success,
            output_preview=(result.output or result.error or "")[:200],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.audit_history.append(entry)
        logger.info(
            "Tool executed: %s success=%s",
            call.name,
            result.success,
        )

        if self.audit_log_path is None:
            return

        record = {
            "timestamp": entry.timestamp,
            "tool": entry.tool_name,
            "arguments": entry.arguments,
            "success": entry.success,
            "output_preview": entry.output_preview,
        }
        with self.audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
