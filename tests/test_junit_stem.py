from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ai_code_repair.repair.log import IterationLog
from ai_code_repair.runner.runner import run_pytest_case

MINIMAL_JUNIT_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="1" failures="0" errors="0" skipped="0">
  <testcase classname="test_example" name="test_one" time="0.001"/>
</testsuite>
"""


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


@patch("ai_code_repair.runner.runner.subprocess.run")
def test_run_pytest_case_default_stem(mock_subprocess_run, tmp_path):
    junit_path = tmp_path / "junit.xml"
    junit_path.write_text(MINIMAL_JUNIT_XML, encoding="utf-8")
    mock_subprocess_run.return_value = type(
        "CompletedProcess", (), {"returncode": 0, "stdout": "", "stderr": ""}
    )()
    report = run_pytest_case(tmp_path, tmp_path)
    assert report.junit_xml_path.endswith("junit.xml")


@patch("ai_code_repair.runner.runner.subprocess.run")
def test_run_pytest_case_custom_stem(mock_subprocess_run, tmp_path):
    junit_path = tmp_path / "junit_iter001.xml"
    junit_path.write_text(MINIMAL_JUNIT_XML, encoding="utf-8")
    mock_subprocess_run.return_value = type(
        "CompletedProcess", (), {"returncode": 0, "stdout": "", "stderr": ""}
    )()
    report = run_pytest_case(tmp_path, tmp_path, junit_stem="junit_iter001")
    assert report.junit_xml_path.endswith("junit_iter001.xml")


def test_iteration_log_junit_xml_path_field():
    log = _make_iteration_log(junit_xml_path="/some/path/junit_iter001.xml")
    assert log.to_dict()["junit_xml_path"] == "/some/path/junit_iter001.xml"


def test_iteration_log_junit_xml_path_default_none():
    log = _make_iteration_log()
    assert log.to_dict()["junit_xml_path"] is None
