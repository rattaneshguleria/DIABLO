"""Core Diablo conversational agent."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

from core.exceptions import DiabloError
from llm.base import ChatMessage, LLMProvider, LLMResponse
from memory.manager import MemoryManager
from memory.short_term import ShortTermMemory
from tools.executor import ToolExecutor

logger = logging.getLogger("diablo.agents.diablo")

ToolActivityCallback = Callable[[str, str], None]


DIABLO_SYSTEM_PROMPT = """You are Diablo, a personal AI operating system inspired by JARVIS.

Identity:
- Name: Diablo
- Wake words: "Hey Diablo" and "Diablo"

Personality:
- Intelligent, calm, professional, helpful, loyal, efficient, and friendly
- You act as the user's personal AI companion and assistant

Behavior:
- Provide clear, accurate, and actionable responses
- Ask clarifying questions when requirements are ambiguouspython main.py --voicepython main.py --voice
- Explain your reasoning when solving complex problems
- Be concise unless the user asks for detail
- Never claim to have performed real-world actions you did not actually execute
- Prioritize reliability, maintainability, and security in your guidance
- When tools are available, use them to gather real information instead of guessing

Current capabilities:
- Natural conversation and reasoning
- Persistent memory across sessions (facts, preferences, and relevant past context)
- Tool calling for calculations, files, system info, web search, and safe commands
- Desktop control: launch/close apps, screenshots, clipboard, volume, mouse, and keyboard
- Voice assistant: wake words, speech recognition, and spoken responses
- Planning guidance (advisory only, not fully autonomous yet)

You can listen for wake words and speak your responses. You do not yet have vision.
Be honest about current limitations when asked.
"""


@dataclass
class ConversationState:
    """Backward-compatible wrapper around short-term memory."""

    messages: list[ChatMessage] = field(default_factory=list)
    max_messages: int = 20

    def add(self, message: ChatMessage) -> None:
        self.messages.append(message)
        self._trim_history()

    def _trim_history(self) -> None:
        if len(self.messages) <= self.max_messages:
            return

        system_messages = [message for message in self.messages if message.role == "system"]
        non_system = [message for message in self.messages if message.role != "system"]
        keep_count = max(self.max_messages - len(system_messages), 0)
        self.messages = system_messages + non_system[-keep_count:]

    def as_llm_messages(self) -> list[ChatMessage]:
        return list(self.messages)

    def clear(self) -> None:
        self.messages = [message for message in self.messages if message.role == "system"]


class DiabloAgent:
    """
    Primary conversational agent for Diablo.

    Coordinates the system prompt, session history, memory, tools, and LLM provider.
    """

    def __init__(
        self,
        llm: LLMProvider,
        *,
        memory: MemoryManager | None = None,
        tool_executor: ToolExecutor | None = None,
        system_prompt: str = DIABLO_SYSTEM_PROMPT,
        max_history_messages: int = 20,
        stream_responses: bool = True,
        max_tool_steps: int = 5,
        tools_enabled: bool = True,
        on_tool_activity: ToolActivityCallback | None = None,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.tool_executor = tool_executor
        self.stream_responses = stream_responses
        self.max_tool_steps = max_tool_steps
        self.tools_enabled = tools_enabled and tool_executor is not None
        self.on_tool_activity = on_tool_activity

        if memory is not None:
            self.state = memory.short_term
        else:
            self.state = ShortTermMemory(max_messages=max_history_messages)
            self.state.add(ChatMessage(role="system", content=system_prompt))

    def startup_check(self) -> None:
        """Validate provider connectivity and model availability."""
        if not self.llm.is_available():
            raise DiabloError(
                "Ollama is not reachable",
                details="Start Ollama and ensure it is listening on the configured host.",
            )

        if hasattr(self.llm, "ensure_model_available"):
            self.llm.ensure_model_available()  # type: ignore[attr-defined]

    def chat(self, user_input: str) -> str | Iterator[str]:
        """Process user input and return assistant response."""
        cleaned = user_input.strip()
        if not cleaned:
            raise DiabloError("Message cannot be empty")

        self.state.add(ChatMessage(role="user", content=cleaned))
        messages = self._build_llm_messages(cleaned)

        logger.info("User message received (%d chars)", len(cleaned))

        if self.tools_enabled:
            return self._chat_with_tools(cleaned, messages)

        if self.stream_responses:
            return self._stream_response(cleaned, messages)
        return self._complete_response(cleaned, messages)

    def remember(self, text: str) -> str:
        """Store an explicit memory note."""
        if self.memory is None:
            raise DiabloError("Memory is disabled")
        stored = self.memory.remember_note(text)
        return f"Remembered: {stored.value}"

    def forget(self, key: str) -> str:
        """Forget a stored memory by key."""
        if self.memory is None:
            raise DiabloError("Memory is disabled")
        self.memory.forget(key)
        return f"Forgot memory key: {key}"

    def list_memories(self) -> list[str]:
        if self.memory is None:
            raise DiabloError("Memory is disabled")
        return [
            f"[{item.category}] {item.key}: {item.value}"
            for item in self.memory.list_memories()
        ]

    def list_sessions(self) -> list[str]:
        if self.memory is None:
            raise DiabloError("Memory is disabled")
        return [
            f"{item.id[:8]}... | {item.message_count} messages | updated {item.updated_at}"
            for item in self.memory.list_sessions()
        ]

    def list_tools(self) -> list[str]:
        if self.tool_executor is None:
            raise DiabloError("Tools are disabled")
        return self.tool_executor.registry.describe_tools()

    def _build_llm_messages(self, user_message: str) -> list[ChatMessage]:
        messages = self.state.as_llm_messages()
        if self.memory is None:
            return messages

        memory_messages = self.memory.build_memory_messages(user_message)
        if not memory_messages:
            return messages

        system_messages = [message for message in messages if message.role == "system"]
        non_system = [message for message in messages if message.role != "system"]
        return system_messages + memory_messages + non_system

    def _chat_with_tools(self, user_message: str, messages: list[ChatMessage]) -> str:
        if self.tool_executor is None:
            raise DiabloError("Tool executor is not configured")

        tools = self.tool_executor.registry.schemas()
        working_messages = list(messages)

        for step in range(self.max_tool_steps):
            result = self.llm.chat(working_messages, stream=False, tools=tools)
            if not isinstance(result, LLMResponse):
                raise DiabloError("Expected non-streaming LLM response")

            if not result.tool_calls:
                self._finalize_response(user_message, result.content)
                logger.info("Assistant response generated (%d chars)", len(result.content))
                return result.content

            working_messages.append(
                ChatMessage(
                    role="assistant",
                    content=result.content,
                    tool_calls=result.tool_calls,
                )
            )

            for call in result.tool_calls:
                self._notify_tool_activity(call.name, "running")
                tool_result = self.tool_executor.execute(call)
                status = "done" if tool_result.success else "failed"
                self._notify_tool_activity(call.name, status)
                working_messages.append(
                    ChatMessage(
                        role="tool",
                        content=tool_result.to_message_content(),
                        tool_name=call.name,
                    )
                )

            logger.info("Completed tool step %d with %d tool call(s)", step + 1, len(result.tool_calls))

        fallback = (
            "I reached the maximum number of tool steps for this request. "
            "Please try a simpler question or break the task into smaller parts."
        )
        self._finalize_response(user_message, fallback)
        return fallback

    def _notify_tool_activity(self, tool_name: str, status: str) -> None:
        if self.on_tool_activity is not None:
            self.on_tool_activity(tool_name, status)

    def _complete_response(self, user_message: str, messages: list[ChatMessage]) -> str:
        result = self.llm.chat(messages, stream=False)
        if not isinstance(result, LLMResponse):
            raise DiabloError("Expected non-streaming LLM response")

        self._finalize_response(user_message, result.content)
        logger.info("Assistant response generated (%d chars)", len(result.content))
        return result.content

    def _stream_response(
        self,
        user_message: str,
        messages: list[ChatMessage],
    ) -> Iterator[str]:
        stream = self.llm.chat(messages, stream=True)
        if isinstance(stream, LLMResponse):
            raise DiabloError("Expected streaming LLM response")

        chunks: list[str] = []

        def generator() -> Iterator[str]:
            for chunk in stream:
                chunks.append(chunk)
                yield chunk
            full_response = "".join(chunks)
            self._finalize_response(user_message, full_response)
            logger.info("Assistant streamed response (%d chars)", len(full_response))

        return generator()

    def _finalize_response(self, user_message: str, assistant_message: str) -> None:
        self.state.add(ChatMessage(role="assistant", content=assistant_message))
        if self.memory is not None:
            self.memory.store_exchange(user_message, assistant_message)

    def reset_conversation(self) -> None:
        """Clear conversation history while keeping persistent memory."""
        if self.memory is not None:
            self.memory.clear_session()
        else:
            self.state.clear()
        logger.info("Conversation history cleared")

    def shutdown(self) -> None:
        """Release memory resources."""
        if self.memory is not None:
            self.memory.close()

    @property
    def message_count(self) -> int:
        return len(self.state.messages)
