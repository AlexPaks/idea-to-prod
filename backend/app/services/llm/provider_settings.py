import os
from functools import lru_cache

from pydantic import BaseModel


class ProviderSettings(BaseModel):
    llm_provider: str = "openai"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""


@lru_cache(maxsize=1)
def get_provider_settings() -> ProviderSettings:
    return ProviderSettings(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    )
