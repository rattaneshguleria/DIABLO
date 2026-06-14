"""Command-line interface for Diablo."""

from __future__ import annotations

import logging
from collections.abc import Iterator

from agents.diablo_agent import DiabloAgent
from core.exceptions import DiabloError
from tools.base import ConfirmationCallback

logger = logging.getLogger("diablo.ui.cli")

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                         DIABLO v0.4                          ║
║              Personal AI Operating System                    ║
╠══════════════════════════════════════════════════════════════╣
║  Commands:                                                   ║
║    /help      - Show available commands                      ║
║    /clear     - Clear current conversation                   ║
║    /tools     - List available tools                         ║
║    /remember  - Save a fact for future sessions              ║
║    /memories  - List stored memories                         ║
║    /forget    - Remove a stored memory by key                ║
║    /sessions  - List recent conversation sessions            ║
║    /exit      - Exit Diablo                                  ║
╚══════════════════════════════════════════════════════════════╝
"""


def create_cli_callbacks() -> tuple[ConfirmationCallback, callable]:
    """Create CLI callbacks for tool confirmation and activity display."""

    def confirm_callback(message: str) -> bool:
        try:
            answer = input(message).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        return answer in {"y", "yes"}

    def tool_activity_callback(tool_name: str, status: str) -> None:
        if status == "running":
            print(f"[Diablo → using {tool_name}...]", flush=True)
        elif status == "failed":
            print(f"[Diablo → {tool_name} failed]", flush=True)

    return confirm_callback, tool_activity_callback


class DiabloCLI:
    """Interactive terminal chat interface."""

    def __init__(self, agent: DiabloAgent) -> None:
        self.agent = agent

    def run(self) -> None:
        print(BANNER)
        print("Diablo is online. How may I assist you?\n")

        while True:
            try:
                user_input = self._read_input()
            except (EOFError, KeyboardInterrupt):
                print("\nDiablo: Shutting down. Goodbye.")
                break

            if not user_input:
                continue

            if self._handle_command(user_input):
                if user_input.strip().lower() in {"/exit", "/quit", "exit", "quit"}:
                    break
                continue

            try:
                response = self.agent.chat(user_input)
                self._render_response(response)
                print()
            except DiabloError as exc:
                print(f"\nDiablo [error]: {exc}\n")
                logger.exception("Chat error")
            except Exception as exc:  # noqa: BLE001 - last-resort CLI guard
                print(f"\nDiablo [unexpected error]: {exc}\n")
                logger.exception("Unexpected chat error")

    def _handle_command(self, user_input: str) -> bool:
        command = user_input.strip()
        lowered = command.lower()

        if lowered in {"/exit", "/quit", "exit", "quit"}:
            print("Diablo: Goodbye.")
            return True

        if lowered == "/help":
            self._print_help()
            return True

        if lowered == "/clear":
            self.agent.reset_conversation()
            print("Diablo: Conversation history cleared.\n")
            return True

        if lowered == "/tools":
            try:
                tools = self.agent.list_tools()
                if not tools:
                    print("Diablo: No tools are enabled.\n")
                else:
                    print("Diablo: Available tools:")
                    for item in tools:
                        print(f"  - {item}")
                    print()
            except DiabloError as exc:
                print(f"Diablo [error]: {exc}\n")
            return True

        if lowered.startswith("/remember "):
            note = command[len("/remember ") :].strip()
            if not note:
                print("Diablo: Usage: /remember <fact to store>\n")
                return True
            try:
                result = self.agent.remember(note)
                print(f"Diablo: {result}\n")
            except DiabloError as exc:
                print(f"Diablo [error]: {exc}\n")
            return True

        if lowered == "/memories":
            try:
                memories = self.agent.list_memories()
                if not memories:
                    print("Diablo: No stored memories yet.\n")
                else:
                    print("Diablo: Stored memories:")
                    for item in memories:
                        print(f"  - {item}")
                    print()
            except DiabloError as exc:
                print(f"Diablo [error]: {exc}\n")
            return True

        if lowered.startswith("/forget "):
            key = command[len("/forget ") :].strip()
            if not key:
                print("Diablo: Usage: /forget <memory key>\n")
                return True
            try:
                result = self.agent.forget(key)
                print(f"Diablo: {result}\n")
            except DiabloError as exc:
                print(f"Diablo [error]: {exc}\n")
            return True

        if lowered == "/sessions":
            try:
                sessions = self.agent.list_sessions()
                if not sessions:
                    print("Diablo: No sessions stored yet.\n")
                else:
                    print("Diablo: Recent sessions:")
                    for item in sessions:
                        print(f"  - {item}")
                    print()
            except DiabloError as exc:
                print(f"Diablo [error]: {exc}\n")
            return True

        return False

    def _read_input(self) -> str:
        return input("You: ").strip()

    def _render_response(self, response: str | Iterator[str]) -> None:
        print("Diablo: ", end="", flush=True)
        if isinstance(response, str):
            print(response)
            return

        for chunk in response:
            print(chunk, end="", flush=True)
        print()

    @staticmethod
    def _print_help() -> None:
        print(
            """
Available commands:
  /help                Show this help message
  /clear               Clear the current conversation history
  /tools               List available tools
  /remember <fact>     Save a fact for future sessions
  /memories            List stored memories
  /forget <key>        Remove a stored memory by key
  /sessions            List recent conversation sessions
  /exit                Exit Diablo

Tips:
  - Ask Diablo to calculate, read files, search the web, or check system info
  - High-risk commands require confirmation before running
  - Diablo remembers facts and preferences across sessions
  - Ensure Ollama is running before starting Diablo
  - Configure model, memory, and tool settings in .env
"""
        )


def run_cli(agent: DiabloAgent) -> None:
    """Entry helper for CLI mode."""
    cli = DiabloCLI(agent)
    cli.run()
