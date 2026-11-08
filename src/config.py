from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    meteo_api_key: str
    openrouter_api_key: str
    model_name: str = "meta-llama/llama-3.3-70b-instruct"
    max_tokens: int = 150
    max_retries: int = 3
    base_delay: float = 1.0

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )