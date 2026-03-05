# Engineering Problem-Solving Log

A record of real engineering difficulties encountered during development and how they were resolved.

---

## Problem 1: LLM Token Waste — Redundant Context in Prompts

**Date:** Phase 1

**Symptom:** Prompts sent to the LLM included large amounts of redundant or verbose content (e.g., full file dumps, raw pytest output), consuming unnecessary tokens and increasing API cost.

**Root Cause:** The initial prompt builder passed raw test output and full source files directly without any summarization or filtering.

**Fix:** Introduced a `summarize_failures()` function in `src/ai_code_repair/repair/prompt.py` that extracts only the relevant failure information (test name, error type, message) before building the prompt. This keeps the context focused and reduces token usage significantly.

**Files Changed:** `src/ai_code_repair/repair/prompt.py`

---

## Problem 2: Repair Loop Destroys the Original Buggy File

**Date:** Phase 1 MVP

**Symptom:** After a successful repair, the original buggy file in `datasets/mini_bugs/<case>/buggy.py` was overwritten with the fixed version. This made it impossible to re-run the experiment on the same bug without restoring from git.

**Root Cause:** The MVP applied patches directly to the source dataset directory, treating it as the working directory.

**Fix:** Implemented **Workspace Isolation (Strategy C)**. Each repair run now copies the entire case directory to `experiments/<case>/<run_id>/workspace/` before making any changes. A frozen snapshot (`buggy_original.py`) is saved at the start and used for rollback. The `datasets/` directory is never modified.

**Experiment directory structure:**
```
experiments/<case>/<run_id>/
├── workspace/
│   ├── buggy.py              ← working copy (patched each iteration)
│   ├── buggy_original.py     ← frozen snapshot, never touched
│   ├── test_buggy.py
│   └── meta.json
├── junit.xml
└── result.json
```

**Files Changed:** `src/ai_code_repair/repair/loop.py`, `src/ai_code_repair/repair/patcher.py`

---

## Problem 3: pytest Discovers and Runs Test Files Inside `experiments/`

**Date:** Phase 1 polish
**Symptom:** Running `pytest` from the project root caused it to recurse into `experiments/` and pick up workspace test files (e.g., `experiments/<case>/<run_id>/workspace/test_buggy.py`). These tests ran in unexpected states (patched or broken versions), polluting results and causing confusing failures.

**Root Cause:** pytest's default test discovery recursively searches all subdirectories unless told otherwise.

**Fix:** Added `norecursedirs = ["experiments", ".venv"]` to the `[tool.pytest.ini_options]` section in `pyproject.toml`. This prevents pytest from entering experiment workspaces during normal test runs.

**Files Changed:** `pyproject.toml`
