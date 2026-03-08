import os
from functools import lru_cache

from pydantic import BaseModel, field_validator


class ProviderSettings(BaseModel):
    llm_provider: str = "openai"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""

    @field_validator("llm_provider")
    @classmethod
    def _normalize_provider(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("openai_api_key", "gemini_api_key", "anthropic_api_key")
    @classmethod
    def _normalize_keys(cls, value: str) -> str:
        return value.strip()


@lru_cache(maxsize=1)
def get_provider_settings() -> ProviderSettings:
    return ProviderSettings(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    )
