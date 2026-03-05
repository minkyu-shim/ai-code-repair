from __future__ import annotations

import subprocess  # it allows you to run external commands and get the output
import time
import xml.etree.ElementTree as ET  # python built in XML parser
from pathlib import Path
from typing import Tuple, Iterable

from ai_code_repair.runner.report import PytestSummary, RunReport


def _parse_junit_xml(xml_path: Path) -> PytestSummary:
    """
    Parse pytest-generated JUnit XML and compute test counts.
    Supports both <testsuite> and <testsuites> roots.

    If the XML is malformed or incomplete, we treat it as a pytest error.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError:
        # Pytest may write a partial file if it crashes mid-run.
        return PytestSummary(total=0, passed=0, failed=0, errors=1, skipped=0)

    if root.tag == "testsuites":
        tests = failures = errors = skipped = 0
        for suite in root.findall("testsuite"):
            tests += int(suite.attrib.get("tests", "0"))
            failures += int(suite.attrib.get("failures", "0"))
            errors += int(suite.attrib.get("errors", "0"))
            skipped += int(suite.attrib.get("skipped", "0"))
    else:
        tests = int(root.attrib.get("tests", "0"))
        failures = int(root.attrib.get("failures", "0"))
        errors = int(root.attrib.get("errors", "0"))
        skipped = int(root.attrib.get("skipped", "0"))

    passed = max(tests - failures - errors - skipped, 0)

    return PytestSummary(
        total=tests,
        passed=passed,
        failed=failures,
        errors=errors,
        skipped=skipped,
    )


def _build_pytest_cmd(junit_xml_path: Path, pytest_args: Iterable[str]) -> list[str]:
    """
    Build the pytest command as a list suitable for subprocess.run(..., shell=False).
    """
    return [
        "python",
        "-m",
        "pytest",
        "-q",
        "--junitxml",
        str(junit_xml_path),
        *pytest_args,
    ]


def run_pytest_case(
        case_dir: Path,
        report_dir: Path,
        *,
        pytest_args: Tuple[str, ...] = (),
        timeout_seconds: int = 120,
        junit_stem: str = "junit",
) -> RunReport:
    """
    Run pytest inside `case_dir`, write junit.xml to `report_dir`,
    parse it, and return a structured report.
    """
    case_dir = case_dir.resolve()
    report_dir = report_dir.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    junit_xml_path = report_dir / f"{junit_stem}.xml"
    cmd = _build_pytest_cmd(junit_xml_path, pytest_args)

    start = time.perf_counter()

    try:
        completed = subprocess.run(
            cmd,
            cwd=str(case_dir),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        duration = time.perf_counter() - start

        # If pytest crashes before writing XML, still return a report.
        if junit_xml_path.exists():
            summary = _parse_junit_xml(junit_xml_path)
        else:
            summary = PytestSummary(total=0, passed=0, failed=0, errors=1, skipped=0)

        return RunReport(
            case_path=str(case_dir),
            pytest_exit_code=completed.returncode,
            duration_seconds=duration,
            junit_xml_path=str(junit_xml_path),
            stdout=completed.stdout,
            stderr=completed.stderr,
            summary=summary,
        )

    except subprocess.TimeoutExpired as e:
        duration = time.perf_counter() - start

        # Timeout: pytest didn't finish. Treat as an error.
        # stdout/stderr exist on the exception object depending on Python version.
        stdout = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode() if e.stdout else "")
        stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode() if e.stderr else "")

        return RunReport(
            case_path=str(case_dir),
            pytest_exit_code=-1,  # convention: -1 for timeout
            duration_seconds=duration,
            junit_xml_path=str(junit_xml_path),
            stdout=stdout,
            stderr=stderr,
            summary=PytestSummary(total=0, passed=0, failed=0, errors=1, skipped=0),
        )
