from __future__ import annotations

from pathlib import Path


def apply_patch(target: Path, new_content: str) -> Path:
    """
    Validate, backup, and overwrite *target* with *new_content*.

    Steps:
      1. Validate syntax via compile() — raises SyntaxError if invalid.
      2. Write the current file to ``target.with_suffix(".bak.py")``.
      3. Overwrite *target* with *new_content*.
      4. Return the backup path so callers can roll back if needed.
    """
    compile(new_content, str(target), "exec")

    backup = target.with_suffix(".bak.py")
    backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    target.write_text(new_content, encoding="utf-8")

    return backup


def rollback(target: Path, backup: Path) -> None:
    """Restore *target* from *backup*, then delete the backup file."""
    target.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
    backup.unlink()
