from pathlib import Path


class PromptLoader:
    def __init__(self, templates_dir: Path | None = None) -> None:
        if templates_dir is None:
            templates_dir = Path(__file__).resolve().parents[2] / "prompt_templates"
        self._templates_dir = templates_dir

    def load(self, template_name: str) -> str:
        template_path = (self._templates_dir / template_name).resolve()
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template '{template_name}' not found")
        if not template_path.is_file():
            raise FileNotFoundError(f"Prompt template '{template_name}' is not a file")

        return template_path.read_text(encoding="utf-8")

    def render(self, template_name: str, context: dict[str, str]) -> str:
        template = self.load(template_name)
        return template.format(**context)
