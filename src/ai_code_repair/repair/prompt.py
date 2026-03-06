from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

_FAILURE_TAGS = ("failure", "error")
_TRUNCATION_MARKER = "... (truncated)"
_PER_ENTRY_MAX_CHARS = 300


def summarize_failures(junit_xml_path: str, stdout: str, max_chars: int = 2000, stderr: str = "") -> str:
    """
    Produce a compact failure summary from a JUnit XML file.

    For each failed or errored <testcase> the summary contains one line:
        FAILED <classname>.<name>: <assertion message, truncated to 300 chars>

    Falls back to truncated raw stdout when the XML file is absent or malformed.
    The returned string is always capped to `max_chars` characters.
    """
    try:
        xml_path = Path(junit_xml_path)
        if not xml_path.exists():
            raise FileNotFoundError(junit_xml_path)

        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Collect all <testcase> elements regardless of root tag.
        if root.tag == "testsuites":
            testcases = root.findall("testsuite/testcase")
        else:
            testcases = root.findall("testcase")

        lines: list[str] = []
        for tc in testcases:
            for tag in _FAILURE_TAGS:
                child = tc.find(tag)
                if child is None:
                    continue

                classname = tc.attrib.get("classname", "")
                name = tc.attrib.get("name", "")
                test_id = f"{classname}.{name}" if classname else name

                # Prefer the element text body (full traceback) over the
                # shorter inline `message` attribute; fall back gracefully.
                raw_message: str = (child.text or child.attrib.get("message", "")).strip()
                if len(raw_message) > _PER_ENTRY_MAX_CHARS:
                    raw_message = raw_message[:_PER_ENTRY_MAX_CHARS] + _TRUNCATION_MARKER

                lines.append(f"FAILED {test_id}: {raw_message}")
                break  # only one failure/error child per testcase

        summary = "\n".join(lines)

    except Exception:
        # XML absent, malformed, or any other I/O problem — fall back to stdout.
        if len(stdout) > max_chars:
            summary = stdout[:max_chars] + _TRUNCATION_MARKER
        else:
            summary = stdout
        if stderr:
            truncated_stderr = stderr[:2000]
            summary = summary + "\n" + truncated_stderr

    # Final hard cap regardless of the path taken above.
    if len(summary) > max_chars:
        summary = summary[:max_chars] + _TRUNCATION_MARKER

    return summary


def build_prompt(source_code: str, test_output: str, filename: str) -> str:
    """
    Construct the repair prompt sent to the LLM.

    The LLM is instructed to return ONLY the corrected Python source wrapped
    in a ```python ... ``` fenced code block — no explanations, no commentary.
    """
    return f"""You are an expert Python debugger. Your task is to fix a buggy Python file so that its test suite passes.

## File: {filename}

```python
{source_code}
```

## Failing test output

```
{test_output}
```

## Instructions

- Analyse the failing tests and identify the bug(s) in the source above.
- Return ONLY the complete, corrected Python source code.
- Wrap your answer in a single ```python ... ``` fenced code block.
- Do NOT include any explanation, commentary, or additional text — only the fixed code inside the fence.
"""
