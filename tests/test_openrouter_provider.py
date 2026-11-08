import pytest

from src.config import Settings
from src.domain.exceptions import LLMFatalError, LLMTransientError
from src.providers.openrouter_provider import OpenRouterLLMProvider, validate_tool_call


def fake_message():
    return ([
        {
            "role": "system",
            "content": (
                "Use the available tools when needed. "
                "Do not invent tool results."
            ),
        },
        {
            "role": "user",
            "content": "Bonjour",
        },
    ])

def test_3_retries():

    delays = []
    calls = []

    def fake_delays(d):
        delays.append(d)

    def mock_raw_llm(messages, tools):
        calls.append(messages)
        raise LLMTransientError("Erreur simulée.")

    settings = Settings(openrouter_api_key="ABC", meteo_api_key="DEF", max_retries=3, base_delay=1)
    provider = OpenRouterLLMProvider(config=settings, time_sleep=fake_delays)
    provider._raw_llm = mock_raw_llm

    with pytest.raises(LLMTransientError):
        provider.call_llm(fake_message())

    assert len(calls) == 3
    assert delays == [1, 2]


def test_2_retries():
    delays = []
    calls = []

    def fake_delays(d):
        delays.append(d)

    def mock_raw_llm(messages, tools):
        calls.append(messages)
        if len(calls) == 1:
            raise LLMTransientError("Erreur simulée.")
        return {"role": "assistant", "content": "Bonjour !"}

    settings = Settings(openrouter_api_key="ABC", meteo_api_key="DEF", max_retries=3, base_delay=1)
    provider = OpenRouterLLMProvider(config=settings, time_sleep=fake_delays)
    provider._raw_llm = mock_raw_llm

    result = provider.call_llm(fake_message())

    assert result == {"role": "assistant", "content": "Bonjour !"}
    assert len(calls) == 2
    assert delays == [1]


def test_fatal_error():
    delays = []
    def fake_delay(d):
        delays.append(d)

    calls = []
    messages = fake_message()
    def mock_raw_llm(messages, tools):
        calls.append(messages)
        raise LLMFatalError("Erreur simulée.")
    
    settings = Settings(meteo_api_key="DEF", openrouter_api_key="ABC", max_retries=3, base_delay=1.0)
    provider = OpenRouterLLMProvider(config=settings, time_sleep=fake_delay)
    provider._raw_llm = mock_raw_llm

    with pytest.raises(LLMFatalError):
        provider.call_llm(messages)

    assert len(calls) == 1
    assert len(delays) == 0



def test_validate_tool_call_text():
    assistant_message = {"role": "assistant", "content": "Bonjour"}
    validate_tool_call(assistant_message)


def test_validate_tool_call_valid():
    assistant_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": "{\"location\": \"Paris\", \"unit\": \"celsius\"}"
                }
            }
        ]
    }

    validate_tool_call(assistant_message)

def test_validate_tool_call_list():
    assistant_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": "test"
    }
    with pytest.raises(LLMFatalError):
        validate_tool_call(assistant_message)


def test_validate_tool_call_dict():
    assistant_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            "test"
        ]
    }
    with pytest.raises(LLMFatalError):
        validate_tool_call(assistant_message)


def test_validate_tool_call_id():
    assistant_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": "{\"location\": \"Paris\", \"unit\": \"celsius\"}"
                }
            }
        ]
    }
    with pytest.raises(LLMFatalError):
        validate_tool_call(assistant_message)


def test_validate_tool_call_function():
    assistant_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_abc123",
                "type": "function"
            }
        ]
    }
    with pytest.raises(LLMFatalError):
        validate_tool_call(assistant_message)

def test_validate_tool_call_name():
    assistant_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "",
                    "arguments": "{\"location\": \"Paris\", \"unit\": \"celsius\"}"
                }
            }
        ]
    }
    with pytest.raises(LLMFatalError):
        validate_tool_call(assistant_message)


def test_validate_tool_call_name_absent():
    assistant_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "arguments": "{\"location\": \"Paris\", \"unit\": \"celsius\"}"
                }
            }
        ]
    }
    with pytest.raises(LLMFatalError):
        validate_tool_call(assistant_message)


