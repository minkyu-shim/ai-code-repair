from __future__ import annotations

from pathlib import Path

from ai_code_repair.runner.runner import _parse_junit_xml


def test_malformed_tests_attribute(tmp_path: Path):
    xml = '<?xml version="1.0"?>\n<testsuite tests="abc" failures="1" errors="0" skipped="0"/>'
    xml_path = tmp_path / "junit.xml"
    xml_path.write_text(xml, encoding="utf-8")
    summary = _parse_junit_xml(xml_path)
    assert summary.total == 0
    assert summary.failed == 1


def test_malformed_failures_attribute(tmp_path: Path):
    xml = '<?xml version="1.0"?>\n<testsuite tests="3" failures="x" errors="0" skipped="0"/>'
    xml_path = tmp_path / "junit.xml"
    xml_path.write_text(xml, encoding="utf-8")
    summary = _parse_junit_xml(xml_path)
    assert summary.total == 3
    assert summary.failed == 0


def test_malformed_errors_attribute(tmp_path: Path):
    xml = '<?xml version="1.0"?>\n<testsuite tests="3" failures="0" errors="?" skipped="0"/>'
    xml_path = tmp_path / "junit.xml"
    xml_path.write_text(xml, encoding="utf-8")
    summary = _parse_junit_xml(xml_path)
    assert summary.total == 3
    assert summary.errors == 0


def test_malformed_skipped_attribute(tmp_path: Path):
    xml = '<?xml version="1.0"?>\n<testsuite tests="3" failures="0" errors="0" skipped="!"/>'
    xml_path = tmp_path / "junit.xml"
    xml_path.write_text(xml, encoding="utf-8")
    summary = _parse_junit_xml(xml_path)
    assert summary.total == 3
    assert summary.skipped == 0
