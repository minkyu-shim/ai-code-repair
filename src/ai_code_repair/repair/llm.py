from __future__ import annotations

import re
from typing import Any, Protocol

from google import genai


class LLMClient(Protocol):
    def generate(self, prompt: str, *, temperature: float | None = None) -> str: ...


def extract_code(response: str) -> tuple[str, bool]:
    """Extract Python source from LLM response. Returns (code, extraction_failed)."""
    # Tier 1: labeled fence (python / Python / py)
    match = re.search(r"```(?:python|py)\s*\n(.*?)```", response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1), False

    # Tier 2: unlabeled fence
    match = re.search(r"```\s*\n(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1), False

    # Tier 3: fallback — extraction failed
    return response, True


class GeminiClient:
    MODEL = "gemini-2.5-flash"
    DEFAULT_TEMPERATURE: float = 1.0

    def __init__(self, model: str = MODEL) -> None:
        # Reads GEMINI_API_KEY from the environment automatically.
        self._client = genai.Client()
        self._model = model

    def generate(self, prompt: str, *, temperature: float | None = None) -> str:
        """Send a prompt to the Gemini API and return the raw text response."""
        kwargs: dict[str, Any] = {
            "model": self._model,
            "contents": prompt,
        }
        if temperature is not None:
            kwargs["config"] = genai.types.GenerateContentConfig(
                temperature=temperature,
            )
        response = self._client.models.generate_content(**kwargs)
        return response.text


class OpenAIClient:
    def __init__(self, model: str) -> None:
        try:
            import openai  # noqa: F401
        except ImportError:
            raise ImportError("Install openai: pip install 'ai-code-repair[openai]'")
        self._model = model

    def generate(self, prompt: str, *, temperature: float | None = None) -> str:
        import openai

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        response = openai.OpenAI().chat.completions.create(**kwargs)
        return response.choices[0].message.content


class AnthropicClient:
    def __init__(self, model: str) -> None:
        try:
            import anthropic  # noqa: F401
        except ImportError:
            raise ImportError("Install anthropic: pip install 'ai-code-repair[anthropic]'")
        self._model = model

    def generate(self, prompt: str, *, temperature: float | None = None) -> str:
        import anthropic

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 8096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        response = anthropic.Anthropic().messages.create(**kwargs)
        return response.content[0].text


def create_client(model: str) -> LLMClient:
    if model.startswith("gemini-"):
        return GeminiClient(model=model)
    if model.startswith(("gpt-", "o1", "o3", "o4")):
        return OpenAIClient(model=model)
    if model.startswith("claude-"):
        return AnthropicClient(model=model)
    raise ValueError(
        f"Unsupported model '{model}'. Supported prefixes: gemini-, gpt-, o1, o3, o4, claude-"
    )
