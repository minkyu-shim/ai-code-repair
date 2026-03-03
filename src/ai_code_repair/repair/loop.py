from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_code_repair.repair.llm import GeminiClient
from ai_code_repair.repair.log import IterationLog, RepairResult
from ai_code_repair.repair.patcher import apply_patch, rollback
from ai_code_repair.repair.prompt import build_prompt, summarize_failures
from ai_code_repair.runner.report import RunReport
from ai_code_repair.runner.runner import run_pytest_case


@dataclass
class RepairConfig:
    case_dir: Path
    max_iterations: int = 1
    model: str = GeminiClient.MODEL
    timeout_seconds: int = 120
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 1.0


class RepairLoop:
    def __init__(self, config: RepairConfig) -> None:
        self._config = config
        self._client = GeminiClient()

    def run(self) -> RepairResult:
        config = self._config
        case_dir = config.case_dir.resolve()

        # 2. Create a timestamped report directory under experiments/.
        run_id = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_dir = Path("experiments") / case_dir.name / run_id

        start_total = time.perf_counter()
        target_file = "<unknown>"

        iteration_logs: list[dict[str, Any]] = []
        success = False
        fatal_error_type: str | None = None
        fatal_error_message: str | None = None
        initial_summary_dict: dict[str, Any] = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 1,
            "skipped": 0,
        }
        current_summary_dict = dict(initial_summary_dict)

        try:
            # 1. Load meta.json to discover the target file.
            meta = json.loads((case_dir / "meta.json").read_text(encoding="utf-8"))
            target_file = meta["target_file"]
            target_path = case_dir / target_file

            # 3. Run baseline pytest.
            latest_report: RunReport = run_pytest_case(
                case_dir, report_dir, timeout_seconds=config.timeout_seconds
            )
            initial_summary = latest_report.summary
            initial_summary_dict = asdict(initial_summary)
            current_summary_dict = dict(initial_summary_dict)

            # 4. Already passing — nothing to do.
            if initial_summary.failed == 0 and initial_summary.errors == 0:
                success = True

            # 5. Repair loop.
            for iteration in range(1, config.max_iterations + 1):
                if success:
                    break

                iter_start = time.perf_counter()
                pre_patch_summary = dict(current_summary_dict)

                source_code = target_path.read_text(encoding="utf-8")
                test_summary = summarize_failures(
                    latest_report.junit_xml_path, latest_report.stdout
                )
                prompt = build_prompt(source_code, test_summary, target_file)
                raw_response = ""
                new_source = ""
                llm_error_type: str | None = None
                llm_error_message: str | None = None
                llm_retry_count = 0

                for attempt in range(config.llm_max_retries + 1):
                    try:
                        raw_response = self._client.generate(prompt)
                        new_source = GeminiClient.extract_code(raw_response)
                        llm_retry_count = attempt
                        break
                    except Exception as exc:
                        llm_error_type = type(exc).__name__
                        llm_error_message = str(exc)
                        llm_retry_count = attempt
                        if attempt >= config.llm_max_retries:
                            break
                        backoff_seconds = config.llm_retry_backoff_seconds * (2 ** attempt)
                        time.sleep(backoff_seconds)

                # LLM request failed after all retries.
                if llm_error_type is not None and not raw_response:
                    iter_duration = time.perf_counter() - iter_start
                    log = IterationLog(
                        iteration=iteration,
                        prompt=prompt,
                        llm_response="",
                        patch_applied=False,
                        pre_patch_summary=pre_patch_summary,
                        post_patch_summary=None,
                        duration_seconds=iter_duration,
                        model=config.model,
                        llm_error_type=llm_error_type,
                        llm_error_message=llm_error_message,
                        llm_retry_count=llm_retry_count,
                    )
                    iteration_logs.append(log.to_dict())
                    continue

                patch_applied = False
                post_summary_dict: dict[str, Any] | None = None
                backup: Path | None = None

                try:
                    backup = apply_patch(target_path, new_source)
                    patch_applied = True
                except SyntaxError:
                    # LLM produced syntactically invalid code — log and continue.
                    iter_duration = time.perf_counter() - iter_start
                    log = IterationLog(
                        iteration=iteration,
                        prompt=prompt,
                        llm_response=raw_response,
                        patch_applied=False,
                        pre_patch_summary=pre_patch_summary,
                        post_patch_summary=None,
                        duration_seconds=iter_duration,
                        model=config.model,
                        llm_error_type=llm_error_type,
                        llm_error_message=llm_error_message,
                        llm_retry_count=llm_retry_count,
                    )
                    iteration_logs.append(log.to_dict())
                    continue

                # Run tests against the patched file.
                try:
                    post_report = run_pytest_case(
                        case_dir, report_dir, timeout_seconds=config.timeout_seconds
                    )
                    post_summary_obj = post_report.summary
                    post_summary_dict = asdict(post_summary_obj)
                    tests_pass = post_summary_obj.failed == 0 and post_summary_obj.errors == 0

                    if tests_pass:
                        # Clean up the backup — we're done.
                        if backup is not None and backup.exists():
                            backup.unlink()
                        current_summary_dict = post_summary_dict
                        latest_report = post_report
                        success = True
                    else:
                        # Patch did not fix all failures — restore the original.
                        if backup is not None:
                            rollback(target_path, backup)
                        latest_report = post_report
                except Exception:
                    if backup is not None:
                        rollback(target_path, backup)
                    raise

                iter_duration = time.perf_counter() - iter_start
                log = IterationLog(
                    iteration=iteration,
                    prompt=prompt,
                    llm_response=raw_response,
                    patch_applied=patch_applied,
                    pre_patch_summary=pre_patch_summary,
                    post_patch_summary=post_summary_dict,
                    duration_seconds=iter_duration,
                    model=config.model,
                    llm_error_type=llm_error_type,
                    llm_error_message=llm_error_message,
                    llm_retry_count=llm_retry_count,
                )
                iteration_logs.append(log.to_dict())
        except Exception as exc:
            fatal_error_type = type(exc).__name__
            fatal_error_message = str(exc)

        total_duration = time.perf_counter() - start_total

        result = RepairResult(
            case_path=str(case_dir),
            target_file=target_file,
            model=config.model,
            success=success,
            total_iterations=len(iteration_logs),
            iterations=iteration_logs,
            initial_summary=initial_summary_dict,
            final_summary=current_summary_dict,
            total_duration_seconds=total_duration,
            fatal_error_type=fatal_error_type,
            fatal_error_message=fatal_error_message,
        )
        result.save_json(report_dir / "result.json")
        return result
