# AI-Assisted Program Repair Using LLMs

A test-guided, iterative repair framework that uses large language models to automatically fix buggy Python programs.

---

## What It Does

Given a directory containing a buggy Python file and a pytest test suite, the framework:

1. Runs the tests to capture the current failure state.
2. Builds a structured prompt from the failing test output and the buggy source code.
3. Calls an LLM (currently Gemini 2.5 Flash) and extracts the proposed patch.
4. Validates the patch's syntax, applies it inside an isolated workspace directory, and re-runs the tests.
5. If all tests pass, the repair is complete. If they still fail, the workspace copy is restored from the frozen original snapshot and the iteration repeats up to a configurable maximum. The `datasets/` directory is never modified.

Every run produces a structured JSON log under `experiments/` capturing the full prompt, LLM response, test counts before and after each patch, timing, and any errors encountered.

---

## Project Status

**Phase 1 — MVP complete.** The single-model repair loop is working end-to-end: runner, prompt builder, LLM client, patcher, and result logger are all implemented and tested against the `mini_bugs` dataset. Subsequent phases (iterative control, overfitting detection, multi-model benchmarking, stability analysis) are planned — see the [Roadmap](#roadmap) below.

## Phase 1 Acceptance Criteria

The following criteria confirm Phase 1 (Minimal Repair Loop) is complete:

- [x] Pytest runner executes and parses JUnit XML results (`src/ai_code_repair/runner/runner.py`)
- [x] LLM patch generator sends structured prompts to Gemini 2.5 and returns candidate patches (`src/ai_code_repair/repair/llm.py`)
- [x] Patch applier applies patches with syntax validation and rollback support (`src/ai_code_repair/repair/patcher.py`)
- [x] Iterative repair loop: test → patch → re-test, up to N iterations (`src/ai_code_repair/repair/loop.py`)
- [x] Experiment logger emits `result.json` per run with iteration logs (`src/ai_code_repair/repair/log.py`)
- [x] Workspace isolation: `datasets/` is never modified; each run copies to `experiments/<case>/<run_id>/workspace/` (`src/ai_code_repair/repair/loop.py`)
- [x] 2/2 mini bug cases repaired successfully (failures reduced to 0, `success: true` in result.json)
- [x] Rollback verified: failed patches are reverted to original snapshot before next iteration

---

## Architecture Overview

The framework is composed of five modules that form a linear pipeline:

```
datasets/case_XXX/
  buggy.py + test_*.py          ← never modified
        |
        v (copied at run start)
  experiments/case_XXX/<run-id>/workspace/
  buggy.py + buggy_original.py + test_*.py + meta.json
        |
        v
  [Runner]  — runs pytest inside workspace/, parses JUnit XML, returns PytestSummary
        |
        v
  [Prompt]  — builds the LLM repair prompt from source + failure output
        |
        v
  [LLM]     — calls Gemini API, extracts fenced code block from response
        |
        v
  [Patcher] — validates syntax, writes patch to workspace/buggy.py;
              restores from buggy_original.py if post-patch tests still fail
        |
        v
  [Logger]  — serialises IterationLog + RepairResult to JSON
        |
        v
  experiments/case_XXX/<run-id>/
    workspace/  junit.xml  result.json
```

| Module | File | Responsibility |
|---|---|---|
| Runner | `src/ai_code_repair/runner/runner.py` | Execute pytest, parse JUnit XML, return `RunReport` |
| Report types | `src/ai_code_repair/runner/report.py` | `PytestSummary` and `RunReport` dataclasses |
| Prompt | `src/ai_code_repair/repair/prompt.py` | Summarise failures, build LLM prompt string |
| LLM client | `src/ai_code_repair/repair/llm.py` | Wrap Gemini API, extract code from fenced response |
| Patcher | `src/ai_code_repair/repair/patcher.py` | Syntax-validate and apply patches to the workspace copy; rollback restores from `buggy_original.py` |
| Logger | `src/ai_code_repair/repair/log.py` | `IterationLog` and `RepairResult` dataclasses with JSON serialisation |
| Loop | `src/ai_code_repair/repair/loop.py` | Orchestrate the full repair loop using the modules above |

---

## Setup

**Prerequisites**

- Python 3.11 or newer
- A [Google AI Studio](https://aistudio.google.com/) API key for Gemini

**Install**

```bash
git clone <repo-url>
cd ai-code-repair

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e .
```

**Environment variables**

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

`scripts/repair.py` calls `load_dotenv()` on startup, so the key is picked up automatically. Alternatively, export it directly in your shell.

---

## Usage

```bash
python scripts/repair.py --case datasets/mini_bugs/case_001
```

Run up to three repair iterations:

```bash
python scripts/repair.py --case datasets/mini_bugs/case_001 --max-iterations 3
```

Set a custom test timeout (default is 120 seconds):

```bash
python scripts/repair.py --case datasets/mini_bugs/case_002 --timeout 60
```

Control what context the LLM receives on retry iterations (when a patch fails and a new attempt is made):

```bash
# Default: LLM always sees the original buggy code + failures from the last failed patch
python scripts/repair.py --case datasets/mini_bugs/case_001 --max-iterations 3 --context-strategy original_with_failures

# Alternative: LLM sees its own last failed patch + that patch's failures
python scripts/repair.py --case datasets/mini_bugs/case_001 --max-iterations 3 --context-strategy last_patch_with_failures
```

`--context-strategy` accepts `original_with_failures` (default) or `last_patch_with_failures`. The choice has no effect on the first iteration (there is no prior patch yet); it only changes what is shown on retries. This setting is recorded in `result.json` under `context_strategy`.

**Console output**

```
[REPAIRED] datasets/mini_bugs/case_001 — 1 iteration(s)
Result saved to experiments/
```

Possible status labels:

| Label | Meaning |
|---|---|
| `[ALREADY PASSING]` | All tests passed before any LLM call was made |
| `[REPAIRED]` | At least one patch attempt succeeded |
| `[FAILED]` | No patch produced a fully passing suite within the iteration limit |

---

## Dataset Format

Each bug case is a self-contained directory:

```
datasets/mini_bugs/case_001/
    buggy.py        # the file the LLM is asked to repair
    test_buggy.py   # pytest test suite (any file matching test_*.py is discovered)
    meta.json       # metadata consumed by the framework
```

`meta.json` schema:

```json
{
  "target_file": "buggy.py",
  "description": "swapped + and - operators in add and subtract functions"
}
```

- `target_file` — filename (relative to the case directory) that will be patched. This is the only required field.
- `description` — human-readable note about the bug; not used by the framework but useful for dataset curation.

The test files must be runnable with `pytest` from inside the case directory with no additional configuration.

---

## Output

Each run writes to a timestamped subdirectory. All patching and test execution happen inside the `workspace/` subdirectory, so the original `datasets/` files are never modified.

```
experiments/
  case_001/
    20260303T095650Z/
      workspace/
        buggy.py              # working copy (final patched state after repair)
        buggy_original.py     # frozen snapshot of the original buggy file
        test_buggy.py         # copy of the test suite
        meta.json             # copy of case metadata
      junit.xml               # raw pytest JUnit XML from the final test run
      result.json             # full structured result (see schema below)
```

**`result.json` top-level fields**

| Field | Type | Description |
|---|---|---|
| `case_path` | string | Path to the case directory (relative to project root) |
| `target_file` | string | File that was patched |
| `model` | string | LLM model identifier used |
| `success` | bool | Whether all tests passed at the end |
| `total_iterations` | int | Number of LLM calls attempted |
| `initial_summary` | object | Test counts before any patching |
| `final_summary` | object | Test counts after the last run |
| `total_duration_seconds` | float | Wall time for the entire run |
| `iterations` | array | Per-iteration detail (see below) |
| `fatal_error_type` | string\|null | Exception class name if the loop crashed |
| `fatal_error_message` | string\|null | Exception message if the loop crashed |

Each element in `iterations` records: the iteration number, the full prompt sent, the raw LLM response, whether the patch was applied, pre- and post-patch test summaries, duration, model name, and any LLM errors with retry counts.

---

## Project Structure

```
.
├── datasets/
│   └── mini_bugs/
│       ├── case_001/           # buggy.py, test_buggy.py, meta.json
│       └── case_002/           # lset.py, test_lset.py, meta.json
├── experiments/                # auto-created; one subdir per run
├── scripts/
│   └── repair.py               # CLI entry point
├── src/
│   └── ai_code_repair/
│       ├── repair/
│       │   ├── __init__.py
│       │   ├── llm.py          # GeminiClient
│       │   ├── log.py          # IterationLog, RepairResult
│       │   ├── loop.py         # RepairLoop, RepairConfig
│       │   ├── patcher.py      # apply_patch (workspace-scoped; no .bak files)
│       │   └── prompt.py       # build_prompt, summarize_failures
│       └── runner/
│           ├── __init__.py
│           ├── report.py       # PytestSummary, RunReport
│           └── runner.py       # run_pytest_case
├── PROJECT_SPEC.md             # full research specification
├── pyproject.toml
└── README.md
```

---

## Roadmap

The project follows a six-phase research plan. See `PROJECT_SPEC.md` for the full specification.

- [x] **Phase 1 — Minimal Repair Loop**: single-model end-to-end repair, JUnit XML parsing, JSON logging, `mini_bugs` dataset.
- [x] **Phase 2 — Iterative Repair Framework** *(in progress)*: context strategy for retry iterations (`--context-strategy`) implemented; early stopping, temperature tuning, and deterministic vs. stochastic runs planned.
- [ ] **Phase 3 — Overfitting Detection**: hidden test cases, mutation testing, test amplification to catch patches that game the visible suite.
- [ ] **Phase 4 — Multi-Model Benchmarking**: compare GPT-class models, Claude, and Gemini under identical conditions; standardised metrics table.
- [ ] **Phase 5 — Stability Analysis**: run identical cases 10+ times per model, measure patch similarity, success consistency, and variance.
- [ ] **Phase 6 — Dataset Scaling**: expand from `mini_bugs` to larger public benchmarks; evaluate cost and scalability.

---

*Author: Minkyu SHIM — EPITA, Computer Science*
