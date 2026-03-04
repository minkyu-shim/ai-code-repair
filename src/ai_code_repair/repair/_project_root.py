"""Locate the project root by walking up from this file until pyproject.toml is found."""
from __future__ import annotations

from pathlib import Path

_cached_root: Path | None = None


def find_project_root() -> Path:
    """Return the nearest ancestor directory containing ``pyproject.toml``.

    The result is cached after the first successful lookup.

    Raises ``FileNotFoundError`` if no ``pyproject.toml`` is found before
    reaching the filesystem root.
    """
    global _cached_root  # noqa: PLW0603
    if _cached_root is not None:
        return _cached_root

    current = Path(__file__).resolve().parent
    while True:
        if (current / "pyproject.toml").is_file():
            _cached_root = current
            return current
        parent = current.parent
        if parent == current:
            raise FileNotFoundError(
                "Could not locate project root (no pyproject.toml found)"
            )
        current = parent
