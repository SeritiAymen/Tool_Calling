TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Gets the current time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Gets the current temperature in Celsius for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, for example Paris or London."
                    }
                },
                "required": ["city"],
                "additionalProperties": False
            }
        }
    }
]