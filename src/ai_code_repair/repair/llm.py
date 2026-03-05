from __future__ import annotations

import re

from google import genai


class GeminiClient:
    MODEL = "gemini-2.5-flash"

    def __init__(self, model: str = MODEL) -> None:
        # Reads GEMINI_API_KEY from the environment automatically.
        self._client = genai.Client()
        self._model = model

    def generate(self, prompt: str) -> str:
        """Send a prompt to the Gemini API and return the raw text response."""
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
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
