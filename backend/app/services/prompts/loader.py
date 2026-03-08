from pathlib import Path


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt template file does not exist."""


class PromptRenderError(ValueError):
    """Raised when prompt context cannot be rendered safely."""


def _prompts_dir() -> Path:
    return Path(__file__).resolve().parent


def load_prompt(filename: str) -> str:
    prompt_path = (_prompts_dir() / filename).resolve()
    prompts_root = _prompts_dir().resolve()

    if prompts_root not in prompt_path.parents:
        raise PromptNotFoundError(
            f"Prompt path '{filename}' resolves outside prompts directory."
        )

    if not prompt_path.exists() or not prompt_path.is_file():
        raise PromptNotFoundError(
            f"Prompt template '{filename}' was not found in '{prompts_root}'."
        )

    return prompt_path.read_text(encoding="utf-8")


def render_prompt(template: str, context: dict[str, str]) -> str:
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)

    unresolved_tokens = [token for token in _find_tokens(rendered)]
    if unresolved_tokens:
        raise PromptRenderError(
            "Prompt rendering failed; unresolved tokens: "
            + ", ".join(sorted(unresolved_tokens))
        )
    return rendered


def _find_tokens(template: str) -> set[str]:
    tokens: set[str] = set()
    start_index = 0
    while True:
        start = template.find("{{", start_index)
        if start < 0:
            break
        end = template.find("}}", start + 2)
        if end < 0:
            break
        tokens.add(template[start : end + 2])
        start_index = end + 2
    return tokens
