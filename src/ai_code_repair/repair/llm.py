from __future__ import annotations

import re
from typing import Any

from google import genai


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

    @staticmethod
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
