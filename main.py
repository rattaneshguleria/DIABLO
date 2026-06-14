"""
Diablo - Personal AI Operating System

Entry point: CLI chatbot powered by Ollama with memory and tools.
"""

from __future__ import annotations

import argparse
import logging
import sys

from agents.diablo_agent import DIABLO_SYSTEM_PROMPT, DiabloAgent
from config import Settings, get_settings
from core.exceptions import DiabloError
from core.logging_config import setup_logging
from llm.ollama_client import OllamaClient
from memory.manager import MemoryManager
from tools.factory import build_tool_executor
from ui.cli import run_cli

logger = logging.getLogger("diablo.main")


def build_agent(
    settings: Settings,
    *,
    confirm_callback=None,
    tool_activity_callback=None,
) -> DiabloAgent:
    """Construct a configured Diablo agent."""
    llm = OllamaClient(
        host=settings.ollama_host,
        model=settings.ollama_model,
        timeout=settings.ollama_timeout,
        temperature=settings.ollama_temperature,
        max_tokens=settings.ollama_max_tokens,
    )

    memory: MemoryManager | None = None
    if settings.memory_enabled:
        memory = MemoryManager.from_settings(
            settings,
            system_prompt=DIABLO_SYSTEM_PROMPT,
        )

    tool_executor = None
    if settings.tools_enabled:
        tool_executor = build_tool_executor(
            settings,
            confirm_callback=confirm_callback,
        )

    return DiabloAgent(
        llm=llm,
        memory=memory,
        tool_executor=tool_executor,
        max_history_messages=settings.max_history_messages,
        stream_responses=settings.stream_responses,
        max_tool_steps=settings.max_tool_steps,
        tools_enabled=settings.tools_enabled,
        on_tool_activity=tool_activity_callback,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diablo - Personal AI Operating System")
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming responses",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable persistent memory for this session",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Disable tool calling for this session",
    )
    parser.add_argument(
        "--no-desktop",
        action="store_true",
        help="Disable desktop control tools for this session",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify Ollama connectivity and exit",
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Run Diablo in voice assistant mode",
    )
    return parser.parse_args()


def main() -> int:
    """Application entry point."""
    args = parse_args()
    settings = get_settings()

    if args.no_memory:
        settings.memory_enabled = False
    if args.no_tools:
        settings.tools_enabled = False
    if args.no_desktop:
        settings.desktop_control_enabled = False

    setup_logging(
        log_level=settings.log_level,
        log_dir=settings.log_dir,
        log_to_file=settings.log_to_file,
    )

    logger.info("Starting %s v%s", settings.app_name, settings.app_version)

    agent: DiabloAgent | None = None
    try:
        if args.check:
            agent = build_agent(settings)
        else:
            from ui.cli import create_cli_callbacks

            confirm_callback, tool_activity_callback = create_cli_callbacks()
            agent = build_agent(
                settings,
                confirm_callback=confirm_callback,
                tool_activity_callback=tool_activity_callback,
            )

        if args.no_stream or args.voice:
            agent.stream_responses = False

        agent.startup_check()

        if args.check:
            models = agent.llm.list_models()
            print("Diablo check: OK")
            print(f"Ollama host: {settings.ollama_host}")
            print(f"Configured model: {settings.ollama_model}")
            print(f"Available models: {', '.join(models) if models else 'none'}")
            print(f"Memory enabled: {settings.memory_enabled}")
            print(f"Tools enabled: {settings.tools_enabled}")
            print(f"Desktop control: {settings.desktop_control_enabled}")
            if settings.memory_enabled:
                print(f"SQLite database: {settings.data_dir / settings.sqlite_db_path}")
                print(f"Chroma directory: {settings.data_dir / settings.chroma_persist_dir}")
                print(f"Embedding model: {settings.embedding_model}")
            if settings.tools_enabled and agent.tool_executor is not None:
                print(f"Registered tools: {', '.join(agent.tool_executor.registry.list_names())}")
            return 0

        if args.voice:
            from ui.voice import run_voice_interface

            run_voice_interface(agent, settings)
            return 0

        run_cli(agent)
        return 0

    except DiabloError as exc:
        logger.error("%s", exc)
        print(f"Diablo startup failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - top-level guard
        logger.exception("Fatal startup error")
        print(f"Diablo fatal error: {exc}", file=sys.stderr)
        return 1
    finally:
        if agent is not None:
            agent.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
