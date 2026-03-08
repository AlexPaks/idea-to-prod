from pathlib import Path


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt template file does not exist."""


def _prompts_dir() -> Path:
    return Path(__file__).resolve().parent / "templates"


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
