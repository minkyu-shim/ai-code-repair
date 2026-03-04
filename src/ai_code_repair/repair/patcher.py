from __future__ import annotations

from pathlib import Path


def apply_patch(target: Path, new_content: str) -> None:
    """
    Validate syntax and overwrite *target* with *new_content*.
    Raises SyntaxError if *new_content* is syntactically invalid.
    """
    compile(new_content, str(target), "exec")
    target.write_text(new_content, encoding="utf-8")
