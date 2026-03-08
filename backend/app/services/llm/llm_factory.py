from dataclasses import dataclass
from typing import Any

from app.services.llm.provider_settings import ProviderSettings, get_provider_settings


@dataclass(slots=True)
class PlaceholderLLM:
    provider: str
    settings: ProviderSettings

    async def complete(self, prompt: str, **_: Any) -> str:
        # TODO: Wire real provider-specific completion logic.
        return (
            f"[placeholder:{self.provider}] "
            "LLM completion is not implemented yet."
        )


def get_llm() -> PlaceholderLLM:
    """
    Stable factory interface for downstream Agno agents.

    TODO:
    - Return a real provider client object based on `LLM_PROVIDER`.
    - Validate provider-specific API keys.
    - Add retries, rate-limit handling, and timeout controls.
    """
    settings = get_provider_settings()
    return PlaceholderLLM(
        provider=settings.llm_provider.strip().lower(),
        settings=settings,
    )
