from __future__ import annotations

from ai_code_repair.repair.llm import GeminiClient
from ai_code_repair.repair.log import IterationLog


def test_extract_code_python_label():
    response = "```python\ncode\n```"
    assert GeminiClient.extract_code(response) == ("code\n", False)


def test_extract_code_python_label_uppercase():
    response = "```Python\ncode\n```"
    assert GeminiClient.extract_code(response) == ("code\n", False)


def test_extract_code_py_label():
    response = "```py\ncode\n```"
    assert GeminiClient.extract_code(response) == ("code\n", False)


def test_extract_code_unlabeled_fence():
    response = "```\ncode\n```"
    assert GeminiClient.extract_code(response) == ("code\n", False)


def test_extract_code_no_fence():
    response = "just some prose"
    assert GeminiClient.extract_code(response) == ("just some prose", True)


def test_extract_code_trailing_whitespace_after_label():
    response = "```python   \ncode\n```"
    assert GeminiClient.extract_code(response) == ("code\n", False)


def _make_iteration_log(**overrides):
    defaults = dict(
        iteration=1,
        prompt="p",
        llm_response="r",
        patch_applied=False,
        pre_patch_summary={"total": 1, "passed": 0, "failed": 1, "errors": 0, "skipped": 0},
        post_patch_summary=None,
        duration_seconds=0.1,
        model="test-model",
    )
    defaults.update(overrides)
    return IterationLog(**defaults)


def test_iteration_log_extraction_failed_field():
    log = _make_iteration_log(extraction_failed=True)
    result = log.to_dict()
    assert result["extraction_failed"] is True


def test_iteration_log_extraction_failed_default():
    log = _make_iteration_log()
    assert log.to_dict()["extraction_failed"] is False
