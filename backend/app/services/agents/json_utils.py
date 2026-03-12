import json
from typing import Any


class AgentJSONParseError(ValueError):
    """Raised when agent output cannot be parsed as JSON object."""


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = _strip_markdown_fences(text.strip())
    if not cleaned:
        raise AgentJSONParseError("Model response is empty.")

    parsed_direct = _try_parse_json(cleaned)
    if isinstance(parsed_direct, dict):
        return parsed_direct

    decoder = json.JSONDecoder()
    for index, character in enumerate(cleaned):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate

    raise AgentJSONParseError("No valid JSON object found in model response.")


def _strip_markdown_fences(text: str) -> str:
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return text


def _try_parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
