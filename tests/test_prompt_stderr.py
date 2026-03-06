from __future__ import annotations

from pathlib import Path

from ai_code_repair.repair.prompt import summarize_failures


def test_stderr_included_when_xml_missing():
    summary = summarize_failures(
        "/nonexistent/junit.xml", "", stderr="ImportError: No module named 'foo'"
    )
    assert "ImportError: No module named 'foo'" in summary


def test_stderr_truncated_at_2000_chars():
    long_stderr = "E" * 3000
    summary = summarize_failures("/nonexistent/junit.xml", "", stderr=long_stderr)
    e_count = summary.count("E")
    assert e_count <= 2000
    assert e_count >= 1999


def test_stderr_not_included_when_xml_present(tmp_path: Path):
    xml_path = tmp_path / "junit.xml"
    xml = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="1" failures="1" errors="0" skipped="0">
  <testcase classname="test_mod" name="test_one">
    <failure message="assert 1 == 2">AssertionError: assert 1 == 2</failure>
  </testcase>
</testsuite>
"""
    xml_path.write_text(xml, encoding="utf-8")
    summary = summarize_failures(
        str(xml_path), "stdout stuff", stderr="SHOULD_NOT_APPEAR"
    )
    assert "SHOULD_NOT_APPEAR" not in summary
