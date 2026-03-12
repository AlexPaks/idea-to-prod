import importlib
import os
from typing import Any

from app.services.llm.provider_settings import get_provider_settings

SUPPORTED_PROVIDERS = {"openai", "gemini", "anthropic"}


class LLMFactoryError(RuntimeError):
    """Base error for LLM factory failures."""


class UnsupportedProviderError(LLMFactoryError):
    """Raised when provider is not supported."""


class MissingAPIKeyError(LLMFactoryError):
    """Raised when a required API key is missing."""


class ProviderImportError(LLMFactoryError):
    """Raised when provider-specific Agno model cannot be imported."""


def get_llm(provider: str | None = None) -> Any:
    settings = get_provider_settings()
    selected_provider = (provider or settings.llm_provider).strip().lower()

    if selected_provider not in SUPPORTED_PROVIDERS:
        raise UnsupportedProviderError(
            "Unsupported LLM provider "
            f"'{selected_provider}'. Supported providers: {', '.join(sorted(SUPPORTED_PROVIDERS))}."
        )

    if selected_provider == "openai":
        if not settings.openai_api_key:
            raise MissingAPIKeyError(
                "OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'."
            )
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        model_cls = _import_agno_model("agno.models.openai", ["OpenAIChat", "OpenAI"])
        return _instantiate_model(model_cls, os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))

    if selected_provider == "gemini":
        if not settings.gemini_api_key:
            raise MissingAPIKeyError(
                "GEMINI_API_KEY is required when LLM_PROVIDER is 'gemini'."
            )
        os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
        os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key
        model_cls = _import_agno_model("agno.models.google", ["Gemini"])
        return _instantiate_model(model_cls, os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))

    if not settings.anthropic_api_key:
        raise MissingAPIKeyError(
            "ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'."
        )
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
    model_cls = _import_agno_model("agno.models.anthropic", ["Claude"])
    return _instantiate_model(
        model_cls,
        os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
    )


def _import_agno_model(module_name: str, class_names: list[str]) -> type[Any]:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ProviderImportError(
            "Agno provider module import failed for "
            f"'{module_name}'. Ensure 'agno' is installed."
        ) from exc

    for class_name in class_names:
        candidate = getattr(module, class_name, None)
        if candidate is not None:
            return candidate

    raise ProviderImportError(
        f"No supported model class found in '{module_name}'. Tried: {', '.join(class_names)}."
    )


def _instantiate_model(model_cls: type[Any], model_id: str) -> Any:
    init_attempts: list[tuple[tuple[Any, ...], dict[str, Any]]] = [
        ((), {"id": model_id}),
        ((), {"model": model_id}),
        ((model_id,), {}),
        ((), {}),
    ]

    for args, kwargs in init_attempts:
        try:
            return model_cls(*args, **kwargs)
        except TypeError:
            continue

    raise ProviderImportError(
        f"Unable to instantiate Agno model class '{model_cls.__name__}'."
    )
