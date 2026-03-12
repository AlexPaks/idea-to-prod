import os
from functools import lru_cache
from pathlib import Path

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


def _load_backend_env_file() -> None:
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists() or not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if (
            (value.startswith('"') and value.endswith('"'))
            or (value.startswith("'") and value.endswith("'"))
        ) and len(value) >= 2:
            value = value[1:-1]

        os.environ.setdefault(key, value)


@lru_cache(maxsize=1)
def get_provider_settings() -> ProviderSettings:
    _load_backend_env_file()
    return ProviderSettings(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    )
