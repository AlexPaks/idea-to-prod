import inspect
import json
import logging
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.services.agents.json_utils import AgentJSONParseError, extract_json_object
from app.services.llm.llm_factory import get_llm
from app.services.prompts.loader import (
    PromptNotFoundError,
    PromptRenderError,
    load_prompt,
    render_prompt,
)

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)


class AgentSetupError(RuntimeError):
    """Raised when agent setup fails."""


class AgentExecutionError(RuntimeError):
    """Raised when an agent call fails."""


class AgentValidationError(ValueError):
    """Raised when output validation fails."""


@dataclass(slots=True)
class AgentBinding:
    agent: Any
    prompt_template: str


def build_agent(name: str, prompt_file: str, provider: str | None = None) -> AgentBinding:
    logger.info("agent=%s event=prompt_load_start prompt=%s", name, prompt_file)
    try:
        prompt_template = load_prompt(prompt_file)
    except PromptNotFoundError as exc:
        raise AgentSetupError(str(exc)) from exc
    logger.info("agent=%s event=prompt_load_complete", name)

    logger.info("agent=%s event=llm_init_start", name)
    llm = get_llm(provider)
    logger.info("agent=%s event=llm_init_complete", name)

    try:
        from agno.agent import Agent as AgnoAgent
    except ModuleNotFoundError as exc:
        raise AgentSetupError(
            "Agno is not installed. Install the 'agno' package to run agent orchestration."
        ) from exc

    instructions = (
        "You are a structured planning agent. "
        "Return one valid JSON object only with no markdown fences and no prose."
    )

    try:
        agent = AgnoAgent(name=name, model=llm, instructions=instructions)
    except TypeError:
        # Backward compatibility for older Agno versions.
        agent = AgnoAgent(name=name, llm=llm, instructions=instructions)

    return AgentBinding(agent=agent, prompt_template=prompt_template)


def build_prompt(template: str, payload: dict[str, Any]) -> str:
    context = {"input_json": json.dumps(payload, ensure_ascii=False, indent=2)}
    try:
        return render_prompt(template, context)
    except PromptRenderError as exc:
        raise AgentExecutionError(str(exc)) from exc


async def execute_agent(agent: Any, prompt: str) -> Any:
    try:
        result = agent.run(prompt)
        if inspect.isawaitable(result):
            return await result
        return result
    except Exception as exc:
        raise AgentExecutionError(f"Agent run failed: {exc}") from exc


def parse_model_result(stage_name: str, raw_result: Any, model_cls: type[ModelT]) -> ModelT:
    data = _coerce_to_dict(raw_result)
    if not data:
        raise AgentValidationError(
            f"Stage '{stage_name}' returned empty output; expected JSON object."
        )

    try:
        validated = model_cls.model_validate(data)
    except ValidationError as exc:
        raise AgentValidationError(
            f"Stage '{stage_name}' produced invalid '{model_cls.__name__}' payload: {exc}"
        ) from exc

    return validated


def _coerce_to_dict(raw_result: Any) -> dict[str, Any]:
    if isinstance(raw_result, dict):
        return raw_result

    if isinstance(raw_result, BaseModel):
        dumped = raw_result.model_dump()
        if isinstance(dumped, dict):
            return dumped

    for candidate in _text_candidates(raw_result):
        try:
            parsed = extract_json_object(candidate)
            if parsed:
                return parsed
        except AgentJSONParseError:
            continue

    return {}


def _text_candidates(raw_result: Any) -> list[str]:
    candidates: list[str] = []

    if raw_result is None:
        return candidates

    if isinstance(raw_result, str):
        return [raw_result]

    if hasattr(raw_result, "content"):
        content = getattr(raw_result, "content")
        candidates.extend(_normalize_content(content))

    for attribute in ("text", "output_text", "response", "output"):
        value = getattr(raw_result, attribute, None)
        candidates.extend(_normalize_content(value))

    if hasattr(raw_result, "model_dump"):
        try:
            dumped = raw_result.model_dump()
        except Exception:
            dumped = None
        candidates.extend(_normalize_content(dumped))

    return [candidate for candidate in candidates if candidate.strip()]


def _normalize_content(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, dict):
        if "text" in value and isinstance(value["text"], str):
            return [value["text"]]
        return [json.dumps(value, ensure_ascii=False)]

    if isinstance(value, list):
        collected: list[str] = []
        for item in value:
            collected.extend(_normalize_content(item))
        return collected

    return [str(value)]
