from uuid import uuid4

from src.config import Settings
from src.domain.exceptions import LLMError
from src.providers.openrouter_provider import OpenRouterLLMProvider
from src.services.tool_calling_service import ToolCallingService
from src.tools.registry import build_registry
from src.tools.schemas import TOOLS
from src.utils.logger import request_id_var, setup_logging


def main():
    setup_logging()

    settings = Settings()
    provider = OpenRouterLLMProvider(settings)
    registry = build_registry(api_key=settings.meteo_api_key)

    service = ToolCallingService(
        provider = provider,
        registry = registry,
        tools = TOOLS,
        max_steps = 5
    )

    token = request_id_var.set(str(uuid4()))
    try:
        result = service.run("Quelle est la météo à Paris ?")
    except LLMError as error:
        print(f"Échec LLM : {error}")
    else:
        print(result)
    finally:
        request_id_var.reset(token)


if __name__ == "__main__":
    main()