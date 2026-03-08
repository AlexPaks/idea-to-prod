import inspect
import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.services.llm.llm_factory import get_llm
from app.services.prompts.loader import load_prompt

logger = logging.getLogger(__name__)

try:
    from agno.agent import Agent as AgnoAgent
except Exception:  # pragma: no cover - optional dependency
    AgnoAgent = None

ModelT = TypeVar("ModelT", bound=BaseModel)


class _FallbackAgent:
    def __init__(self, name: str) -> None:
        self.name = name

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload


def build_agent(name: str, prompt_file: str) -> Any:
    instructions = load_prompt(prompt_file)

    if AgnoAgent is None:
        logger.warning(
            "Agno Agent unavailable; using fallback agent '%s'. Install agno to enable runtime.",
            name,
        )
        return _FallbackAgent(name)

    try:
        return AgnoAgent(
            name=name,
            llm=get_llm(),
            instructions=instructions,
        )
    except Exception:  # pragma: no cover - defensive path
        logger.exception("Failed to initialize Agno agent '%s'; using fallback.", name)
        return _FallbackAgent(name)


async def execute_agent(agent: Any, payload: dict[str, Any]) -> Any:
    result = agent.run(payload)
    if inspect.isawaitable(result):
        return await result
    return result


def parse_model_result(
    stage_name: str,
    raw_result: Any,
    model_cls: type[ModelT],
    fallback: ModelT,
) -> ModelT:
    data = _coerce_to_dict(raw_result)
    if not data:
        logger.warning(
            "Agent stage '%s' returned empty payload; using fallback result.",
            stage_name,
        )
        return fallback

    try:
        return model_cls.model_validate(data)
    except ValidationError:
        logger.exception(
            "Agent stage '%s' returned invalid payload for %s; using fallback.",
            stage_name,
            model_cls.__name__,
        )
        return fallback


def _coerce_to_dict(raw_result: Any) -> dict[str, Any]:
    if isinstance(raw_result, dict):
        return raw_result

    content = getattr(raw_result, "content", None)
    if isinstance(content, dict):
        return content

    if isinstance(content, str):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed

    text = getattr(raw_result, "text", None)
    if isinstance(text, str):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed

    if isinstance(raw_result, str):
        try:
            parsed = json.loads(raw_result)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed

    return {}
