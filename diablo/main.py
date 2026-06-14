"""
Diablo - Personal AI Operating System

Phase 1 entry point: CLI chatbot powered by Ollama.
"""

from __future__ import annotations

import argparse
import logging
import sys

from agents.diablo_agent import DiabloAgent
from config import get_settings
from core.exceptions import DiabloError
from core.logging_config import setup_logging
from llm.ollama_client import OllamaClient
from ui.cli import run_cli

logger = logging.getLogger("diablo.main")


def build_agent() -> DiabloAgent:
    """Construct a configured Diablo agent."""
    settings = get_settings()

    llm = OllamaClient(
        host=settings.ollama_host,
        model=settings.ollama_model,
        timeout=settings.ollama_timeout,
        temperature=settings.ollama_temperature,
        max_tokens=settings.ollama_max_tokens,
    )

    return DiabloAgent(
        llm=llm,
        max_history_messages=settings.max_history_messages,
        stream_responses=settings.stream_responses,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diablo - Personal AI Operating System")
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming responses",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify Ollama connectivity and exit",
    )
    return parser.parse_args()


def main() -> int:
    """Application entry point."""
    args = parse_args()
    settings = get_settings()

    setup_logging(
        log_level=settings.log_level,
        log_dir=settings.log_dir,
        log_to_file=settings.log_to_file,
    )

    logger.info("Starting %s v%s", settings.app_name, settings.app_version)

    try:
        agent = build_agent()

        if args.no_stream:
            agent.stream_responses = False

        agent.startup_check()

        if args.check:
            models = agent.llm.list_models()
            print("Diablo check: OK")
            print(f"Ollama host: {settings.ollama_host}")
            print(f"Configured model: {settings.ollama_model}")
            print(f"Available models: {', '.join(models) if models else 'none'}")
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


if __name__ == "__main__":
    raise SystemExit(main())
