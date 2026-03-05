from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ContextStrategy(str, Enum):
    """Strategy for what context to feed the LLM on retry iterations."""

    ORIGINAL_WITH_FAILURES = "original_with_failures"
    LAST_PATCH_WITH_FAILURES = "last_patch_with_failures"


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
    llm_error_type: str | None = None
    llm_error_message: str | None = None
    llm_retry_count: int = 0
    extraction_failed: bool = False
    junit_xml_path: str | None = None
    context_strategy: str = "original_with_failures"

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
    context_strategy: str = "original_with_failures"
    fatal_error_type: str | None = None
    fatal_error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save_json(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self.to_dict(), indent=2), encoding="utf-8"
        )
