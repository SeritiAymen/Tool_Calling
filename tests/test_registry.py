from src.tools.registry import handle_tool_call


def make_tool_call(name="get_current_time", arguments="{}"):
    return {
        "id": "call_id",
        "type": "function",
        "function": {"name": name, "arguments": arguments},
    }



def fake_time():
    return "10:00:00"


def test_handle_tool_call_success():

    result = handle_tool_call(
        registry={"get_current_time": fake_time},
        tool_call = make_tool_call()
    )

    assert result["tool_call_id"] == "call_id"
    assert result["role"] == "tool"
    assert result["content"] == "10:00:00" 


def test_handle_tool_call_unknown_tool():

    result = handle_tool_call(
        registry={},
        tool_call = make_tool_call()
    )

    assert result["content"] == "Error: Unknown tool 'get_current_time'."


def test_handle_tool_call_invalid_json():

    result = handle_tool_call(
        registry={"get_current_time": fake_time},
        tool_call = make_tool_call(arguments="{")
    )

    assert result["content"] == "Error: Tool arguments must be valid JSON."


def test_handle_tool_call_tool_fail():

    def error_fake_time():
        raise RuntimeError("Panne Simulée.")
        
    result = handle_tool_call(
        registry={"get_current_time": error_fake_time},
        tool_call = make_tool_call()
    )

    assert result["content"] == "Error: Tool 'get_current_time' failed."


def test_handle_tool_call_arguments_not_dict():
    result = handle_tool_call(
        registry = {"get_current_time": fake_time},
        tool_call = make_tool_call(arguments='[1, 2]')
    )

    assert result["content"] == "Error: Tool arguments must be a dictionary."