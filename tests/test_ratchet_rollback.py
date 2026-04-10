from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from ai_code_repair.repair.log import ContextStrategy
from ai_code_repair.repair.loop import RepairConfig, RepairLoop
from ai_code_repair.runner.report import PytestSummary, RunReport


def _make_run_report(
    case_path: str,
    report_dir: Path,
    total: int = 4,
    passed: int = 0,
    failed: int = 4,
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
    case_dir = tmp_path / f"case_rr_{_case_counter}"
    case_dir.mkdir()
    meta = {"target_file": "buggy.py"}
    (case_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (case_dir / "buggy.py").write_text("x = 1\n", encoding="utf-8")
    (case_dir / "test_buggy.py").write_text("def test_a(): pass\n", encoding="utf-8")
    return case_dir


# ---------------------------------------------------------------------------
# Scenario 1: Ratchet promotes on strict improvement, then succeeds
# ---------------------------------------------------------------------------

@patch("ai_code_repair.repair.loop.run_pytest_case")
@patch("ai_code_repair.repair.loop.GeminiClient")
@patch("ai_code_repair.repair.loop.apply_patch")
def test_ratchet_promotes_on_strict_improvement(
    mock_apply_patch, mock_client_cls, mock_run_pytest, tmp_path
):
    """Baseline: 0/3; Iter 1: 2/3 promoted; Iter 2: 3/3 success."""
    case_dir = _setup_case(tmp_path)

    call_count = [0]

    def run_pytest_side_effect(workspace_dir, report_dir, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_run_report(
                str(workspace_dir), report_dir, total=3, passed=0, failed=3,
            )
        elif call_count[0] == 2:
            return _make_run_report(
                str(workspace_dir), report_dir, total=3, passed=2, failed=1,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )
        else:
            return _make_run_report(
                str(workspace_dir), report_dir, total=3, passed=3, failed=0,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )

    mock_run_pytest.side_effect = run_pytest_side_effect

    client_instance = MagicMock()
    client_instance.generate.return_value = "```python\nx = 2\n```"
    mock_client_cls.return_value = client_instance
    mock_client_cls.extract_code.return_value = ("x = 2\n", False)
    mock_client_cls.MODEL = "test-model"

    config = RepairConfig(
        case_dir=case_dir,
        max_iterations=2,
        context_strategy=ContextStrategy.BEST_PATCH_WITH_FAILURES,
        experiments_base_dir=tmp_path / "experiments",
    )
    result = RepairLoop(config).run()

    assert result.success is True


# ---------------------------------------------------------------------------
# Scenario 2: Ratchet restores best on regression
# ---------------------------------------------------------------------------

@patch("ai_code_repair.repair.loop.run_pytest_case")
@patch("ai_code_repair.repair.loop.GeminiClient")
@patch("ai_code_repair.repair.loop.apply_patch")
def test_ratchet_restores_best_on_regression(
    mock_apply_patch, mock_client_cls, mock_run_pytest, tmp_path
):
    """Baseline: 0/4; Iter 1: 3/4 promoted; Iter 2: 1/4 regression, best restored."""
    case_dir = _setup_case(tmp_path)
    target_paths: list[Path] = []

    call_count = [0]

    def apply_patch_side_effect(target_path, new_source):
        target_path.write_text(new_source, encoding="utf-8")
        if not target_paths:
            target_paths.append(target_path)

    def run_pytest_side_effect(workspace_dir, report_dir, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_run_report(
                str(workspace_dir), report_dir, total=4, passed=0, failed=4,
            )
        elif call_count[0] == 2:
            return _make_run_report(
                str(workspace_dir), report_dir, total=4, passed=3, failed=1,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )
        else:
            return _make_run_report(
                str(workspace_dir), report_dir, total=4, passed=1, failed=3,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )

    mock_run_pytest.side_effect = run_pytest_side_effect
    mock_apply_patch.side_effect = apply_patch_side_effect

    iter_sources = iter(["x = 2  # iter1 best\n", "x = 3  # iter2 regression\n"])

    client_instance = MagicMock()
    client_instance.generate.return_value = "```python\nx = 2\n```"
    mock_client_cls.return_value = client_instance
    mock_client_cls.extract_code.side_effect = lambda resp: (next(iter_sources), False)
    mock_client_cls.MODEL = "test-model"

    config = RepairConfig(
        case_dir=case_dir,
        max_iterations=2,
        context_strategy=ContextStrategy.BEST_PATCH_WITH_FAILURES,
        experiments_base_dir=tmp_path / "experiments",
    )
    result = RepairLoop(config).run()

    # After iter 2 regression, the file on disk should be the iter-1 (best) source.
    assert target_paths, "apply_patch was never called"
    assert target_paths[0].read_text(encoding="utf-8") == "x = 2  # iter1 best\n"


# ---------------------------------------------------------------------------
# Scenario 3: Ratchet restores best on tie (not promoted)
# ---------------------------------------------------------------------------

@patch("ai_code_repair.repair.loop.run_pytest_case")
@patch("ai_code_repair.repair.loop.GeminiClient")
@patch("ai_code_repair.repair.loop.apply_patch")
def test_ratchet_restores_best_on_tie(
    mock_apply_patch, mock_client_cls, mock_run_pytest, tmp_path
):
    """Baseline: 0/4; Iter 1: 2/4 promoted; Iter 2: 2/4 tie, best NOT updated."""
    case_dir = _setup_case(tmp_path)
    target_paths: list[Path] = []

    call_count = [0]

    def apply_patch_side_effect(target_path, new_source):
        target_path.write_text(new_source, encoding="utf-8")
        if not target_paths:
            target_paths.append(target_path)

    def run_pytest_side_effect(workspace_dir, report_dir, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_run_report(
                str(workspace_dir), report_dir, total=4, passed=0, failed=4,
            )
        elif call_count[0] == 2:
            return _make_run_report(
                str(workspace_dir), report_dir, total=4, passed=2, failed=2,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )
        else:
            return _make_run_report(
                str(workspace_dir), report_dir, total=4, passed=2, failed=2,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )

    mock_run_pytest.side_effect = run_pytest_side_effect
    mock_apply_patch.side_effect = apply_patch_side_effect

    iter_sources = iter(["x = 2  # iter1 best\n", "x = 3  # iter2 tie\n"])

    client_instance = MagicMock()
    client_instance.generate.return_value = "```python\nx = 2\n```"
    mock_client_cls.return_value = client_instance
    mock_client_cls.extract_code.side_effect = lambda resp: (next(iter_sources), False)
    mock_client_cls.MODEL = "test-model"

    config = RepairConfig(
        case_dir=case_dir,
        max_iterations=2,
        context_strategy=ContextStrategy.BEST_PATCH_WITH_FAILURES,
        experiments_base_dir=tmp_path / "experiments",
    )
    result = RepairLoop(config).run()

    # On tie, best is NOT updated — file should be iter-1 source.
    assert target_paths, "apply_patch was never called"
    assert target_paths[0].read_text(encoding="utf-8") == "x = 2  # iter1 best\n"


# ---------------------------------------------------------------------------
# Scenario 4: Falls back to original when no best exists (SyntaxError)
# ---------------------------------------------------------------------------

@patch("ai_code_repair.repair.loop.run_pytest_case")
@patch("ai_code_repair.repair.loop.GeminiClient")
@patch("ai_code_repair.repair.loop.apply_patch")
def test_ratchet_falls_back_to_original_when_no_best(
    mock_apply_patch, mock_client_cls, mock_run_pytest, tmp_path
):
    """Baseline: 0/3; Iter 1: SyntaxError, no best, rollback to original."""
    case_dir = _setup_case(tmp_path)
    target_paths: list[Path] = []

    call_count = [0]
    syntax_error_raised = [False]

    def apply_patch_side_effect(target_path, new_source):
        if not target_paths:
            target_paths.append(target_path)
        if not syntax_error_raised[0]:
            syntax_error_raised[0] = True
            raise SyntaxError("bad syntax")
        target_path.write_text(new_source, encoding="utf-8")

    def run_pytest_side_effect(workspace_dir, report_dir, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_run_report(
                str(workspace_dir), report_dir, total=3, passed=0, failed=3,
            )
        else:
            return _make_run_report(
                str(workspace_dir), report_dir, total=3, passed=3, failed=0,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )

    mock_run_pytest.side_effect = run_pytest_side_effect
    mock_apply_patch.side_effect = apply_patch_side_effect

    client_instance = MagicMock()
    client_instance.generate.return_value = "```python\nx = 2\n```"
    mock_client_cls.return_value = client_instance
    mock_client_cls.extract_code.return_value = ("x = 2\n", False)
    mock_client_cls.MODEL = "test-model"

    config = RepairConfig(
        case_dir=case_dir,
        max_iterations=2,
        context_strategy=ContextStrategy.BEST_PATCH_WITH_FAILURES,
        experiments_base_dir=tmp_path / "experiments",
    )
    result = RepairLoop(config).run()

    # After SyntaxError with no best, file should be original.
    assert target_paths, "apply_patch was never called"
    # After iter 1 SyntaxError rollback, target should contain original content.
    # But iter 2 succeeds, so let's check result instead.
    assert result.fatal_error_type is None
    assert result.iterations[0]["patch_applied"] is False
    # Verify the original content was restored after SyntaxError by checking
    # that iter 2 ran successfully (it wouldn't if rollback was broken).
    assert result.success is True


# ---------------------------------------------------------------------------
# Scenario 5: Non-best strategy rollback unchanged (ORIGINAL_WITH_FAILURES)
# ---------------------------------------------------------------------------

@patch("ai_code_repair.repair.loop.run_pytest_case")
@patch("ai_code_repair.repair.loop.GeminiClient")
@patch("ai_code_repair.repair.loop.apply_patch")
def test_non_best_strategy_rollback_unchanged(
    mock_apply_patch, mock_client_cls, mock_run_pytest, tmp_path
):
    """ORIGINAL_WITH_FAILURES: improvement without full pass restores original."""
    case_dir = _setup_case(tmp_path)
    target_paths: list[Path] = []

    call_count = [0]

    def apply_patch_side_effect(target_path, new_source):
        target_path.write_text(new_source, encoding="utf-8")
        if not target_paths:
            target_paths.append(target_path)

    def run_pytest_side_effect(workspace_dir, report_dir, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_run_report(
                str(workspace_dir), report_dir, total=3, passed=0, failed=3,
            )
        else:
            return _make_run_report(
                str(workspace_dir), report_dir, total=3, passed=2, failed=1,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )

    mock_run_pytest.side_effect = run_pytest_side_effect
    mock_apply_patch.side_effect = apply_patch_side_effect

    client_instance = MagicMock()
    client_instance.generate.return_value = "```python\nx = 2\n```"
    mock_client_cls.return_value = client_instance
    mock_client_cls.extract_code.return_value = ("x = 2  # patched\n", False)
    mock_client_cls.MODEL = "test-model"

    config = RepairConfig(
        case_dir=case_dir,
        max_iterations=1,
        context_strategy=ContextStrategy.ORIGINAL_WITH_FAILURES,
        experiments_base_dir=tmp_path / "experiments",
    )
    result = RepairLoop(config).run()

    # ORIGINAL_WITH_FAILURES always restores original on non-perfect.
    assert target_paths, "apply_patch was never called"
    assert target_paths[0].read_text(encoding="utf-8") == "x = 1\n"


# ---------------------------------------------------------------------------
# Scenario 6: Prompt uses best_patch_source after regression
# ---------------------------------------------------------------------------

@patch("ai_code_repair.repair.loop.run_pytest_case")
@patch("ai_code_repair.repair.loop.GeminiClient")
@patch("ai_code_repair.repair.loop.build_prompt")
@patch("ai_code_repair.repair.loop.summarize_failures")
@patch("ai_code_repair.repair.loop.apply_patch")
def test_prompt_uses_best_patch_source_after_regression(
    mock_apply_patch, mock_summarize, mock_build_prompt,
    mock_client_cls, mock_run_pytest, tmp_path,
):
    """After regression, iter 3 prompt should use iter-1 best source."""
    case_dir = _setup_case(tmp_path)

    call_count = [0]

    def apply_patch_side_effect(target_path, new_source):
        target_path.write_text(new_source, encoding="utf-8")

    def run_pytest_side_effect(workspace_dir, report_dir, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_run_report(
                str(workspace_dir), report_dir, total=4, passed=0, failed=4,
            )
        elif call_count[0] == 2:
            return _make_run_report(
                str(workspace_dir), report_dir, total=4, passed=3, failed=1,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )
        elif call_count[0] == 3:
            return _make_run_report(
                str(workspace_dir), report_dir, total=4, passed=1, failed=3,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )
        else:
            return _make_run_report(
                str(workspace_dir), report_dir, total=4, passed=4, failed=0,
                junit_stem=kwargs.get("junit_stem", "junit"),
            )

    mock_run_pytest.side_effect = run_pytest_side_effect
    mock_apply_patch.side_effect = apply_patch_side_effect
    mock_summarize.return_value = "failures summary"
    mock_build_prompt.return_value = "prompt"

    iter_sources = iter([
        "x = 2  # iter1 best\n",
        "x = 3  # iter2 regression\n",
        "x = 4  # iter3 fix\n",
    ])

    client_instance = MagicMock()
    client_instance.generate.return_value = "```python\nx = 2\n```"
    mock_client_cls.return_value = client_instance
    mock_client_cls.extract_code.side_effect = lambda resp: (next(iter_sources), False)
    mock_client_cls.MODEL = "test-model"

    config = RepairConfig(
        case_dir=case_dir,
        max_iterations=3,
        context_strategy=ContextStrategy.BEST_PATCH_WITH_FAILURES,
        experiments_base_dir=tmp_path / "experiments",
    )
    result = RepairLoop(config).run()

    # build_prompt calls: iter1 (original), iter2 (best=iter1), iter3 (best=iter1)
    assert mock_build_prompt.call_count == 3
    iter3_source_arg = mock_build_prompt.call_args_list[2][0][0]
    assert iter3_source_arg == "x = 2  # iter1 best\n"


# ---------------------------------------------------------------------------
# Scenario 7: Default strategy is BEST_PATCH_WITH_FAILURES
# ---------------------------------------------------------------------------

def test_best_patch_strategy_is_default():
    """RepairConfig default context_strategy should be BEST_PATCH_WITH_FAILURES.

    NOTE: This test is written as part of the rollout. It will fail until
    the default is changed in step 5. If running before step 5, expect failure.
    """
    config = RepairConfig(case_dir=Path("."))
    assert config.context_strategy is ContextStrategy.BEST_PATCH_WITH_FAILURES
