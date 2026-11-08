from typing import Any, Protocol

Message = dict[str, Any]

class LLMProviderProtocol(Protocol):
    def call_llm(
            self,
            messages: list[Message],
            tools: list[dict[str, Any]] | None = None
    ) -> Message:
        ...