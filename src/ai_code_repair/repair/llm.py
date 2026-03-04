from __future__ import annotations

import re

from google import genai


class GeminiClient:
    MODEL = "gemini-2.5-flash"

    def __init__(self) -> None:
        # Reads GEMINI_API_KEY from the environment automatically.
        self._client = genai.Client()

    def generate(self, prompt: str) -> str:
        """Send a prompt to the Gemini API and return the raw text response."""
        response = self._client.models.generate_content(
            model=self.MODEL,
            contents=prompt,
        )
        return response.text

    @staticmethod
    def extract_code(response: str) -> str:
        """
        Strip ```python ... ``` fences from the LLM response.

        Falls back to returning the raw response unchanged if no fence is found,
        so callers always receive something they can attempt to apply.
        """
        match = re.search(r"```python\s*\n(.*?)```", response, re.DOTALL)
        if match:
            return match.group(1)
        return response
