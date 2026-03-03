from __future__ import annotations


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
