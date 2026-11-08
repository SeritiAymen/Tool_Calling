import json
import time
from functools import partial

from src.tools.implementations import get_current_time, get_weather
from src.utils.logger import get_logger

logger = get_logger(__name__)

def build_registry(api_key: str):
    return {
        "get_current_time": get_current_time,
        "get_weather": partial(get_weather, api_key=api_key)
    }


def execute_tool(
        registry: dict,
        tool_name: str,
        arguments: dict
) -> str:
    if tool_name not in registry:
        logger.warning("tool_unknown", extra={"props": {"tool_name": tool_name}})
        return f"Error: Unknown tool '{tool_name}'."

    if not isinstance(arguments, dict):
        logger.warning("tool_arguments_type", extra={"props": {"tool_name": tool_name, "arguments_type": type(arguments).__name__}})
        return "Error: Tool arguments must be a dictionary."

    tool_function = registry[tool_name]

    start_time = time.perf_counter()
    try:
        result = tool_function(**arguments)
    except Exception as e: # noqa: BLE001 - frontière : un échec d'outil devient une observation
        logger.warning("tool_error", extra={"props": {"tool_name": tool_name, "error_type": type(e).__name__}})
        return f"Error: Tool '{tool_name}' failed."
    else:
        logger.info("tool_executed", extra={"props": {
            "tool_name": tool_name,
            "duration_ms": round((time.perf_counter()-start_time)*1000, 2)
        }})


    return str(result)

def handle_tool_call(registry: dict, tool_call: dict) -> dict:
    call_id = tool_call["id"]
    function_info = tool_call["function"]
    tool_name = function_info["name"]
    raw_arguments = function_info.get("arguments", "{}")

    try:
        arguments = json.loads(raw_arguments)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("tool_invalid_json", extra={"props": {"tool_name": tool_name, "error_type": type(e).__name__}})
        result = "Error: Tool arguments must be valid JSON."
    else:
        result = execute_tool(registry, tool_name, arguments)

    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": result
    }