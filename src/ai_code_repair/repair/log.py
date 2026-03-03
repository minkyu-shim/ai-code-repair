from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class IterationLog:
    iteration: int
    prompt: str
    llm_response: str
    patch_applied: bool
    pre_patch_summary: dict[str, Any]
    post_patch_summary: dict[str, Any] | None
    duration_seconds: float
    model: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepairResult:
    case_path: str
    target_file: str
    model: str
    success: bool
    total_iterations: int
    iterations: list[dict[str, Any]]
    initial_summary: dict[str, Any]
    final_summary: dict[str, Any]
    total_duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save_json(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self.to_dict(), indent=2), encoding="utf-8"
        )
