import time
from collections.abc import Callable
from typing import Any

import requests

from src.config import Settings
from src.domain.exceptions import LLMFatalError, LLMTransientError
from src.domain.protocols import Message
from src.utils.logger import get_logger

logger = get_logger(__name__)

class OpenRouterLLMProvider:
    def __init__(self, config: Settings, time_sleep: Callable[[float], None] = time.sleep):
        self.config = config
        self.time_sleep = time_sleep
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {config.openrouter_api_key}",
            "Content-Type": "application/json"
        }



    def _raw_llm(
            self,
            messages: list[Message],
            tools: list[dict[str, Any]] | None = None
    ) -> Message:
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": 0.0
        }

        if tools is not None:
            payload["tools"] = tools


        start_time = time.perf_counter()
        try:

            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload,
                timeout=(3.0,30.0)
            )

            if response.status_code == 401:
                raise LLMFatalError("Clé OpenRouter invalide (401).")
            if response.status_code == 429:
                raise LLMTransientError("Rate limit atteint (429).")
            
            response.raise_for_status()

        except requests.Timeout as e:
            raise LLMTransientError("Délai d'attente LLM dépassé.") from e

        except requests.HTTPError as e:
            status = e.response.status_code

            if status >= 500:
                raise LLMTransientError(f"Erreur serveur distante {status}.") from e
            raise LLMFatalError(f"Erreur client bloquante {status}.") from e

        except requests.RequestException as e:
            raise LLMTransientError("Réseau inaccessible.") from e

        try:
            data = response.json()
            usage = data.get("usage", {})
            message = data["choices"][0]["message"]

        except (ValueError, KeyError, IndexError, TypeError) as e:
            raise LLMFatalError("Réponse LLM inexploitable.") from e

        if not isinstance(message, dict):
            raise LLMFatalError("Le message LLM doit être un dictionnaire.")

        if message.get("role") != "assistant":
            raise LLMFatalError("Le message reçu n'est pas un message assistant.")

        if not message.get("tool_calls") and not isinstance(message.get("content"), str):
                raise LLMFatalError("Réponse sans texte ni demande d'outil.")

        validate_tool_call(message)
        logger.info("llm_call_success", extra={"props": {
            "latency_ms": round((time.perf_counter()-start_time)*1000, 2),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "model": self.config.model_name
        }})
        return message


    def call_llm(self, messages: list[Message], tools: list[dict[str, Any]] | None = None) -> Message:

        for attempt in range(1,self.config.max_retries+1):
            delay = self.config.base_delay*(2**(attempt-1))
            
            try:
                result = self._raw_llm(messages, tools)

                return result
            
            except LLMTransientError as e:
                if attempt == self.config.max_retries:
                    logger.error("llm_retry_exhausted", extra={"props": {
                        "attempts": attempt,
                        "error_type": type(e).__name__
                    }})
                    raise

                logger.warning("llm_retry_started", extra={"props": {
                    "attempt": attempt,
                    "delay_seconds": delay,
                    "error_type": type(e).__name__
                }})
                self.time_sleep(delay)
            except LLMFatalError as e:
                logger.error("llm_fatal_aborted", extra={"props": {"error_type": type(e).__name__}})
                raise


def validate_tool_call(assistant_message: dict[str,Any]):
    tool_calls = assistant_message.get("tool_calls", [])
    if not isinstance(tool_calls, list):
        raise LLMFatalError("tool_calls est inexistante ou n'est pas une liste.")
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            raise LLMFatalError("tool_call doit être un dictionnaire.")
        call_id = tool_call.get("id")
        if not isinstance(call_id, str):
            raise LLMFatalError("l'id du tool_call est inexistant ou mal formaté.")
        function = tool_call.get("function")
        if not isinstance(function, dict):
            raise LLMFatalError("l'objet 'function' du tool_call est inexistant ou mal formaté.")
        name = function.get("name")
        if not isinstance(name, str) or name == "":
            raise LLMFatalError("le nom de la fonction du tool_call est inexistant ou mal formaté.")