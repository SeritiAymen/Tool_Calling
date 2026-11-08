from typing import Any

from src.domain.protocols import LLMProviderProtocol, Message
from src.tools.registry import handle_tool_call
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ToolCallingService:
    def __init__(
            self,
            provider: LLMProviderProtocol,
            registry: dict,
            tools: list[dict[str, Any]],
            max_steps: int = 5
    ):
        if max_steps < 1:
            raise ValueError("max_steps doit être supérieur ou égal à 1.")

        self.provider = provider
        self.registry = registry
        self.tools = tools
        self.max_steps = max_steps


    def run(
            self,
            user_prompt: str
    ) -> str:
        if not user_prompt.strip():
            raise ValueError("La question est vide.")

        messages: list[Message] = [
            {
                "role": "system",
                "content": (
                    "Use the available tools when needed. "
                    "Do not invent tool results."
                ),
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        logger.info("conversation_started", extra={"props": {
            "max_steps": self.max_steps
        }})
        for step in range(self.max_steps):
            assistant_message = self.provider.call_llm(
                messages,
                tools=self.tools,
            )

            tool_calls = assistant_message.get("tool_calls")

            if not tool_calls:

                logger.info("final_answer_received", extra={"props" : {
                    "steps_used": step+1
                }})

                return assistant_message["content"]


            messages.append(assistant_message)

            for tool_call in tool_calls:
                logger.info("tool_requested", extra={"props": {
                    "steps_used" : step+1,
                    "tool_name": tool_call["function"]["name"]
                }})
                tool_result = handle_tool_call(registry=self.registry, tool_call=tool_call)
                messages.append(tool_result)

        logger.error("max_steps_reached", extra = {"props": {
            "max_steps": self.max_steps
        }})

        return (
            f"Exécution interrompue : limite de "
            f"{self.max_steps} appels LLM atteinte."
        )
