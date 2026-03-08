import json
from typing import Any
from urllib import error, parse, request


class LLMError(Exception):
    """Base error for LLM client failures."""


class LLMNetworkError(LLMError):
    """Raised for network/API transport failures."""


class LLMRateLimitError(LLMError):
    """Raised when provider rate limits requests."""


class LLMInvalidResponseError(LLMError):
    """Raised when provider response cannot be parsed."""


class LLMConfigurationError(LLMError):
    """Raised when required provider configuration is missing."""


class LLMClient:
    def __init__(
        self,
        provider: str,
        openai_api_key: str = "",
        gemini_api_key: str = "",
        openai_model: str = "gpt-4.1-mini",
        gemini_model: str = "gemini-2.0-flash",
        timeout_seconds: float = 30.0,
    ) -> None:
        self._provider = provider.strip().lower()
        self._openai_api_key = openai_api_key.strip()
        self._gemini_api_key = gemini_api_key.strip()
        self._openai_model = openai_model
        self._gemini_model = gemini_model
        self._timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise LLMInvalidResponseError("Prompt cannot be empty")

        if self._provider == "openai":
            return self._generate_openai(prompt)

        if self._provider == "gemini":
            return self._generate_gemini(prompt)

        raise LLMConfigurationError(f"Unsupported LLM_PROVIDER '{self._provider}'")

    def _generate_openai(self, prompt: str) -> str:
        if not self._openai_api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is required for provider 'openai'")

        payload = {
            "model": self._openai_model,
            "input": prompt,
        }
        headers = {
            "Authorization": f"Bearer {self._openai_api_key}",
            "Content-Type": "application/json",
        }

        response = self._post_json(
            "https://api.openai.com/v1/responses",
            payload,
            headers=headers,
        )

        output_text = response.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        # Fallback parsing for response shape variants.
        output = response.get("output", [])
        if isinstance(output, list):
            texts: list[str] = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                contents = item.get("content", [])
                if not isinstance(contents, list):
                    continue
                for content in contents:
                    if not isinstance(content, dict):
                        continue
                    text = content.get("text")
                    if isinstance(text, str) and text.strip():
                        texts.append(text.strip())
            if texts:
                return "\n\n".join(texts)

        raise LLMInvalidResponseError("OpenAI response did not contain text output")

    def _generate_gemini(self, prompt: str) -> str:
        if not self._gemini_api_key:
            raise LLMConfigurationError("GEMINI_API_KEY is required for provider 'gemini'")

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        query = parse.urlencode({"key": self._gemini_api_key})
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._gemini_model}:generateContent?{query}"
        )

        response = self._post_json(endpoint, payload, headers={"Content-Type": "application/json"})
        candidates = response.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise LLMInvalidResponseError("Gemini response missing candidates")

        first = candidates[0]
        if not isinstance(first, dict):
            raise LLMInvalidResponseError("Gemini candidate format invalid")

        content = first.get("content", {})
        if not isinstance(content, dict):
            raise LLMInvalidResponseError("Gemini content format invalid")

        parts = content.get("parts", [])
        if not isinstance(parts, list):
            raise LLMInvalidResponseError("Gemini parts format invalid")

        texts: list[str] = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())

        if texts:
            return "\n\n".join(texts)
        raise LLMInvalidResponseError("Gemini response did not contain text output")

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        http_request = request.Request(url, data=data, headers=headers, method="POST")

        try:
            with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 429:
                raise LLMRateLimitError(f"Rate limited by provider: {body}") from exc
            raise LLMNetworkError(f"Provider HTTP error {exc.code}: {body}") from exc
        except error.URLError as exc:
            raise LLMNetworkError(f"Provider network error: {exc}") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise LLMInvalidResponseError("Provider returned non-JSON response") from exc

        if not isinstance(parsed, dict):
            raise LLMInvalidResponseError("Provider returned invalid JSON payload")

        return parsed
