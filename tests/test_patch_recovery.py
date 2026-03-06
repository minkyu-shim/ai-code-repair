from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from ai_code_repair.repair.loop import RepairConfig, RepairLoop
from ai_code_repair.runner.report import PytestSummary, RunReport


def _make_run_report(
    case_path: str,
    report_dir: Path,
    total: int = 3,
    passed: int = 0,
    failed: int = 3,
    errors: int = 0,
    skipped: int = 0,
    junit_stem: str = "junit",
) -> RunReport:
    summary = PytestSummary(
        total=total, passed=passed, failed=failed, errors=errors, skipped=skipped
    )
    junit_path = report_dir / f"{junit_stem}.xml"
    junit_path.write_text("<testsuite/>", encoding="utf-8")
    return RunReport(
        case_path=case_path,
        pytest_exit_code=1 if (failed or errors) else 0,
        duration_seconds=0.01,
        junit_xml_path=str(junit_path),
        stdout="test output",
        stderr="",
        summary=summary,
    )


_case_counter = 0


def _setup_case(tmp_path: Path) -> Path:
    global _case_counter
    _case_counter += 1
    case_dir = tmp_path / f"case_pr_{_case_counter}"
    case_dir.mkdir()
    meta = {"target_file": "buggy.py"}
    (case_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (case_dir / "buggy.py").write_text("x = 1\n", encoding="utf-8")
    (case_dir / "test_buggy.py").write_text("def test_a(): pass\n", encoding="utf-8")
    return case_dir


@patch("ai_code_repair.repair.loop.run_pytest_case")
@patch("ai_code_repair.repair.loop.GeminiClient")
@patch("ai_code_repair.repair.loop.apply_patch")
def test_syntax_error_is_recoverable(
    mock_apply_patch, mock_client_cls, mock_run_pytest, tmp_path
):
    case_dir = _setup_case(tmp_path)

    call_count = [0]

    def run_pytest_side_effect(workspace_dir, report_dir, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_run_report(str(workspace_dir), report_dir, total=3, passed=0, failed=3)
        else:
            return _make_run_report(
                str(workspace_dir), report_dir, total=3, passed=3, failed=0,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )

    mock_run_pytest.side_effect = run_pytest_side_effect
    mock_apply_patch.side_effect = [SyntaxError("bad syntax"), None]

    client_instance = MagicMock()
    client_instance.generate.return_value = "```python\nx = 2\n```"
    mock_client_cls.return_value = client_instance
    mock_client_cls.extract_code.return_value = ("x = 2\n", False)
    mock_client_cls.MODEL = "test-model"

    config = RepairConfig(case_dir=case_dir, max_iterations=2)
    loop = RepairLoop(config)
    result = loop.run()

    assert result.fatal_error_type is None
    assert result.iterations[0]["patch_applied"] is False


@patch("ai_code_repair.repair.loop.run_pytest_case")
@patch("ai_code_repair.repair.loop.GeminiClient")
@patch("ai_code_repair.repair.loop.apply_patch")
def test_oserror_is_recoverable(
    mock_apply_patch, mock_client_cls, mock_run_pytest, tmp_path
):
    case_dir = _setup_case(tmp_path)

    call_count = [0]

    def run_pytest_side_effect(workspace_dir, report_dir, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_run_report(str(workspace_dir), report_dir, total=3, passed=0, failed=3)
        else:
            return _make_run_report(
                str(workspace_dir), report_dir, total=3, passed=3, failed=0,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )

    mock_run_pytest.side_effect = run_pytest_side_effect
    mock_apply_patch.side_effect = [OSError("permission denied"), None]

    client_instance = MagicMock()
    client_instance.generate.return_value = "```python\nx = 2\n```"
    mock_client_cls.return_value = client_instance
    mock_client_cls.extract_code.return_value = ("x = 2\n", False)
    mock_client_cls.MODEL = "test-model"

    config = RepairConfig(case_dir=case_dir, max_iterations=2)
    loop = RepairLoop(config)
    result = loop.run()

    assert result.fatal_error_type is None
    assert result.iterations[0]["patch_applied"] is False


@patch("ai_code_repair.repair.loop.run_pytest_case")
@patch("ai_code_repair.repair.loop.GeminiClient")
@patch("ai_code_repair.repair.loop.apply_patch")
def test_oserror_triggers_rollback(
    mock_apply_patch, mock_client_cls, mock_run_pytest, tmp_path
):
    case_dir = _setup_case(tmp_path)
    original_content = "x = 1\n"

    call_count = [0]
    captured_content = []

    def run_pytest_side_effect(workspace_dir, report_dir, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_run_report(str(workspace_dir), report_dir, total=3, passed=0, failed=3)
        else:
            target = workspace_dir / "buggy.py"
            captured_content.append(target.read_text(encoding="utf-8"))
            return _make_run_report(
                str(workspace_dir), report_dir, total=3, passed=3, failed=0,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )

    mock_run_pytest.side_effect = run_pytest_side_effect
    mock_apply_patch.side_effect = [OSError("permission denied"), None]

    client_instance = MagicMock()
    client_instance.generate.return_value = "```python\nx = 2\n```"
    mock_client_cls.return_value = client_instance
    mock_client_cls.extract_code.return_value = ("x = 2\n", False)
    mock_client_cls.MODEL = "test-model"

    config = RepairConfig(case_dir=case_dir, max_iterations=2)
    loop = RepairLoop(config)
    result = loop.run()

    assert captured_content[0] == original_content
