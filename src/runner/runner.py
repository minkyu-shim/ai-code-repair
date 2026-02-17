from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
from typing import Any, Sequence


class Runner:
    def __init__(self, test_command: Sequence[str] | None = None) -> None:
        self.test_command = list(test_command or ["python", "-m", "pytest", "-q"])

    def run(
        self,
        program_dir: str | Path,
        patch: str | Path,
        report_path: str | Path | None = None,
        keep_patched_dir: bool = False,
    ) -> dict[str, Any]:
        source_dir = Path(program_dir).resolve()
        if not source_dir.is_dir():
            raise FileNotFoundError(f"Program directory not found: {source_dir}")

        before = self._run_tests(source_dir)

        patched_dir = Path(tempfile.mkdtemp(prefix=f"{source_dir.name}_patched_"))
        shutil.rmtree(patched_dir, ignore_errors=True)
        shutil.copytree(source_dir, patched_dir)

        patch_applied = False
        patch_error = None
        after = None

        try:
            self._apply_patch(patched_dir, patch)
            patch_applied = True
            after = self._run_tests(patched_dir)
        except Exception as exc:  # pragma: no cover
            patch_error = str(exc)

        status = self._status(before, after, patch_applied)

        report: dict[str, Any] = {
            "name": source_dir.name,
            "program_dir": str(source_dir),
            "patched_dir": str(patched_dir) if keep_patched_dir else None,
            "before": before,
            "after": after,
            "patch_applied": patch_applied,
            "patch_error": patch_error,
            "status": status,
        }

        if report_path is not None:
            output_path = Path(report_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        if not keep_patched_dir:
            shutil.rmtree(patched_dir, ignore_errors=True)

        return report

    def _run_tests(self, project_dir: Path) -> dict[str, Any]:
        result = subprocess.run(
            self.test_command,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "passed": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    @staticmethod
    def _apply_patch(project_dir: Path, patch: str | Path) -> None:
        patch_path = Path(patch)
        temp_path: Path | None = None

        if patch_path.is_file():
            diff_file = patch_path.resolve()
        else:
            temp = tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False, encoding="utf-8")
            temp.write(str(patch))
            temp.close()
            temp_path = Path(temp.name)
            diff_file = temp_path

        try:
            result = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", str(diff_file)],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                error_text = result.stderr.strip() or result.stdout.strip() or "patch apply failed"
                raise RuntimeError(error_text)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    @staticmethod
    def _status(before: dict[str, Any], after: dict[str, Any] | None, patch_applied: bool) -> str:
        if not patch_applied or after is None:
            return "patch_failed"
        if (not before["passed"]) and after["passed"]:
            return "repaired"
        if before["passed"] and (not after["passed"]):
            return "regressed"
        return "not_repaired"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simple test runner for patch evaluation.")
    parser.add_argument("--program", required=True, help="Buggy program folder")
    parser.add_argument("--patch", required=True, help="Patch file path (.diff/.patch) or inline diff text")
    parser.add_argument("--report", required=True, help="Output JSON path")
    parser.add_argument(
        "--test-command",
        default="python -m pytest -q",
        help="Command used to run tests",
    )
    parser.add_argument("--keep-patched-dir", action="store_true", help="Keep copied patched folder")
    args = parser.parse_args(argv)

    runner = Runner(test_command=shlex.split(args.test_command))
    report = runner.run(
        program_dir=args.program,
        patch=args.patch,
        report_path=args.report,
        keep_patched_dir=args.keep_patched_dir,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

