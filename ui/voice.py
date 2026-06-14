"""Voice mode interface for Diablo."""

from __future__ import annotations

import logging

from agents.diablo_agent import DiabloAgent
from config import Settings
from core.exceptions import DiabloError
from system.voice import VoiceAssistant

logger = logging.getLogger("diablo.ui.voice")

EXIT_COMMANDS = {"exit", "quit", "stop", "goodbye"}


def run_voice_interface(agent: DiabloAgent, settings: Settings) -> None:
    voice = VoiceAssistant.from_settings(settings)
    agent.stream_responses = False

    print("Diablo voice assistant is active.")
    print("Say 'Hey Diablo' or 'Diablo' to wake the assistant.")
    voice.speak("Diablo is now listening. Say Hey Diablo when you need me.")

    while True:
        try:
            voice.wait_for_wake_word()
            voice.speak("Yes?")
            command = voice.listen_command()
            normalized = command.strip().lower()

            if not normalized:
                voice.speak("I did not hear a command. Please try again.")
                continue

            if normalized in EXIT_COMMANDS:
                voice.speak("Goodbye.")
                break

            response = agent.chat(command)
            text_response = response if isinstance(response, str) else "".join(response)
            voice.speak(text_response)

        except KeyboardInterrupt:
            voice.speak("Shutting down. Goodbye.")
            break
        except DiabloError as exc:
            logger.exception("Voice assistant error")
            print(f"Diablo [voice error]: {exc}")
            voice.speak("I encountered an error. Please check the console.")

    print("Voice assistant stopped.")
