from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional


# used dataclass for cleaner code, you can use __init__ bla bla bla
@dataclass(frozen=True)
class PytestSummary:
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int

class RunReport:
    case_path: str
    pytest_exit_code: int
    duration_seconds: float
    junit_xml_path: str
    stdout: str
    stderr: str
    summary: PytestSummary

    def to_dict(self) -> Dict[str, Any]:
        # asdict converts dataclass' instances into a dictionary
        d = asdict(self)
        d["case_path"] = str(self.case_path)
        d["junit_xml_path"] = str(self.junit_xml_path)
        return d

    def save_json(self, output_path: Path) -> None:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")