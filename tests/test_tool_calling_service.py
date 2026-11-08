from copy import deepcopy

import pytest

from src.domain.exceptions import LLMTransientError
from src.services.tool_calling_service import ToolCallingService


class ScriptedProvider:
    """Faux provider qui joue une liste de réponses dans l'ordre."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.received_messages = []

    def call_llm(self, messages, tools=None):
        self.received_messages.append(deepcopy(messages))
        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response


def tool_request(call_id):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": "get_current_time", "arguments": "{}"},
            }
        ],
    }


def final_answer(text):
    return {"role": "assistant", "content": text}


def make_service(provider, executed_tools, max_steps=5):
    def fake_time():
        executed_tools.append("get_current_time")
        return "10:00:00"
        
    return ToolCallingService(
        provider=provider,
        registry={"get_current_time": fake_time},
        tools=[],
        max_steps=max_steps,
        )


def test_tool_cycle():
    provider = ScriptedProvider([
        tool_request("call_test"),
        final_answer("Il est 10:00:00."),
    ])
    executed_tools = []
    service = make_service(provider, executed_tools, max_steps=2)

    result = service.run("Quelle heure est-il ?")

    assert result == "Il est 10:00:00."
    assert executed_tools == ["get_current_time"]
    assert len(provider.received_messages) == 2

    first_call = provider.received_messages[0]
    assert len(first_call) == 2

    second_call = provider.received_messages[1]
    assert second_call[-2]["tool_calls"][0]["id"] == "call_test"
    assert second_call[-1] == {
        "role": "tool",
        "tool_call_id": "call_test",
        "content": "10:00:00",
    }




def test_direct_answer_without_tool():
    provider = ScriptedProvider([final_answer("Bonjour !")])
    executed_tools = []
    service = make_service(provider, executed_tools)
    
    result = service.run("Bonjour")
    
    assert result == "Bonjour !"
    assert len(provider.received_messages) == 1
    assert executed_tools == []


def test_stops_at_max_steps():
    provider = ScriptedProvider([tool_request("call_1"), tool_request("call_2")])
    executed_tools = []
    service = make_service(provider, executed_tools, max_steps=2)

    result = service.run("Quelle heure est-il ?")

    assert len(provider.received_messages) == 2
    assert executed_tools == ["get_current_time", "get_current_time"]
    assert result.startswith("Exécution interrompue")


def test_provider_error_propagates():
    provider = ScriptedProvider([LLMTransientError("Panne simulée.")])
    executed_tools = []
    service = make_service(provider, executed_tools)

    with pytest.raises(LLMTransientError):
        service.run("Quelle heure est-il ?")

    assert executed_tools == []