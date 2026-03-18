# Codebase Review Guide

Use this guide when you want to re-learn the project after time away.

The goal is not to read every file. The goal is to build one clear mental model:

1. What enters the system
2. How the repair loop runs
3. Which modules support the loop
4. What artifacts are written
5. How the three context strategies differ

If you follow this in order and write down your answers, you should have a stable understanding of the project flow before going deeper into Phase 2.

## How To Use This Guide

For each step:

1. Read this file
2. Answer these questions in your own notes
3. Do not move on until you can answer without looking

Keep one scratch note with these headings:

- Entry point
- Main loop
- Data flow
- Artifacts written
- Context strategies
- Failure and rollback behavior
- Open questions

## Step 1: Rebuild The Big Picture

### Read this file

- `README.md`

### Answer these questions

- What problem does this project solve?
- What is the end-to-end pipeline from buggy code to `result.json`?
- What does the project write into `experiments/`?
- What counts as a successful repair?
- Which parts are Phase 1 working code, and which parts are future research plans?

### Read this file

- `PROJECT_SPEC.md`

### Answer these questions

- What is the high-level architecture?
- What is the difference between Phase 1 and Phase 2?
- What research questions matter for iterative repair?
- Which metrics or behaviors does the spec care about?

### Checkpoint

Write a 5-line summary of the project without looking at the files.

If you cannot do that, repeat Step 1.

## Step 2: Learn The Runtime Entry Point

### Read this file

- `scripts/repair.py`

### Answer these questions

- What CLI arguments exist?
- What defaults are currently important?
- How is `RepairConfig` constructed?
- Where does execution hand off into the real application code?
- What does the CLI print at the end, and what does it not print?

### Checkpoint

Write one sentence that starts with:

`When I run python scripts/repair.py ...`

and finishes by describing what happens next.

## Step 3: Learn The Core Loop First

This is the most important step in the entire review.

### Read this file

- `src/ai_code_repair/repair/loop.py`

### Answer these questions

- How is the run directory created?
- Why is the case copied into `workspace/`?
- Where does the target file path come from?
- When is baseline pytest run?
- Under what condition does the loop skip all LLM calls?
- How is the prompt source selected for each iteration?
- How is the failure summary selected for each iteration?
- When is the LLM called?
- How is code extracted from the LLM response?
- What happens if patch application raises `SyntaxError` or `OSError`?
- What happens after a patch is tested?
- When does the loop mark `success = True`?
- What gets restored on rollback for each strategy?
- What gets written to `result.json` at the end?

### Required exercise

Write the loop in exactly 11 steps:

1. Load case metadata
2. Copy case into workspace
3. Save snapshots
4. Run baseline tests
5. Choose prompt context
6. Summarize failures
7. Call LLM
8. Apply patch
9. Re-run tests
10. Accept, reject, or retry
11. Save structured results

If you cannot explain each of those using actual variables from `loop.py`, stay on this step.

## Step 4: Attach The Support Modules To The Loop

Do not read these as isolated utilities. Read each one and connect it back to the exact place where `loop.py` uses it.

### Read this file

- `src/ai_code_repair/runner/runner.py`

### Answer these questions

- How does pytest get executed?
- What inputs does `run_pytest_case(...)` need?
- What outputs come back from a test run?
- Which parts of the returned report are later used by `loop.py`?

### Read this file

- `src/ai_code_repair/runner/report.py`

### Answer these questions

- What is stored in `PytestSummary`?
- What is stored in `RunReport`?
- Which fields are used for prompt building?
- Which fields are used for final reporting?

### Read this file

- `src/ai_code_repair/repair/prompt.py`

### Answer these questions

- How are failures summarized from JUnit XML?
- What gets truncated, and why?
- What exact information is given to the LLM?
- What information is not included in the prompt?

### Read this file

- `src/ai_code_repair/repair/llm.py`

### Answer these questions

- Which model client is wrapped here?
- What does `generate(...)` return?
- How does `extract_code(...)` work?
- What happens if the response is not in a fenced code block?
- What metadata is currently not being logged from the provider?

### Read this file

- `src/ai_code_repair/repair/patcher.py`

### Answer these questions

- What makes a patch valid enough to write?
- What exceptions can this module trigger back into the loop?
- Does this module decide whether a patch is accepted semantically?

### Read this file

- `src/ai_code_repair/repair/log.py`

### Answer these questions

- What is stored per iteration?
- What is stored at run level?
- Which fields explain strategy choice?
- Which fields are missing if you want stronger experiment auditing?

### Checkpoint

Make a table with three columns:

- Module
- Used by which line or section of `loop.py`
- Why it exists

## Step 5: Anchor Everything In One Small Bug Case

### Read this file

- `datasets/mini_bugs/case_001/meta.json`

### Answer these questions

- What is the target file?
- What assumptions does the loop make about this metadata?

### Read this file

- `datasets/mini_bugs/case_001/buggy.py`

### Answer these questions

- What is broken in the target code?
- Could the LLM fix it with only code + failing test output?

### Read this file

- `datasets/mini_bugs/case_001/test_buggy.py`

### Answer these questions

- What behavior do the tests enforce?
- What would a correct patch need to change?

### Checkpoint

Explain how `case_001` flows through the loop from baseline failure to repaired output.

## Step 6: Trace One Real Experimental Run

Use one real run to map artifacts back to the code.

### Read this file

- `experiments/case_005/20260305T215059Z/result.json`

### Answer these questions

- How many iterations happened?
- What did each iteration send to the LLM?
- What was the pre-patch summary for each iteration?
- What was the post-patch summary for each iteration?
- What does this tell you about how the loop carries state forward?

### Read this file

- `experiments/case_005/20260305T215059Z/junit_iter001.xml`

### Answer these questions

- Which failures remained after iteration 1?
- How does that map to the summarized prompt content?

### Read this file

- `experiments/case_005/20260305T215059Z/junit_iter002.xml`

### Answer these questions

- Did iteration 2 improve, stall, or regress?
- Which loop policy seems responsible?

### Read this file

- `experiments/case_005/NOTES.md`

### Answer these questions

- What interpretation was recorded for this run?
- Which parts are solid observations?
- Which parts are hypotheses that still need verification?

### Checkpoint

Write one paragraph that starts with:

`case_005 matters because...`

## Step 7: Use Tests As Design Documentation

These tests tell you what behavior the project is trying to preserve.

### Read this file

- `tests/test_summary_accounting.py`

### Answer these questions

- What does the project consider the “current” summary after a failed attempt?
- What behavior is intentional versus accidental?
- Which assertions encode policy rather than mechanics?

### Read this file

- `tests/test_patch_recovery.py`

### Answer these questions

- What failure modes are covered when patch application goes wrong?
- What rollback guarantees already exist?

### Read this file

- `tests/test_ratchet_rollback.py`

### Answer these questions

- What does `best_patch_with_failures` add to the system?
- When is a patch promoted to “best”?
- What happens on regression?
- What happens on tie?
- What parts of the strategy affect prompt source versus rollback behavior?

### Read this file

- `tests/test_junit_parsing.py`

### Answer these questions

- What assumptions are made about JUnit XML structure?
- How robust is failure summarization?

### Read this file

- `tests/test_extract_code.py`

### Answer these questions

- What response formats from the LLM are supported?
- What happens when extraction fails?

### Checkpoint

Write down three current design rules you learned from tests.

Example format:

- The loop treats ...
- The project logs ...
- The rollback policy ...

## Step 8: Understand The Three Context Strategies

After you have read the loop and ratchet tests, come back to this comparison.

### Read this file

- `src/ai_code_repair/repair/log.py`
- `src/ai_code_repair/repair/loop.py`
- `tests/test_ratchet_rollback.py`

### Answer these questions

- For `original_with_failures`, what source code is shown on retry?
- For `last_patch_with_failures`, what source code is shown on retry?
- For `best_patch_with_failures`, what source code is shown on retry?
- Which strategy changes only prompt context?
- Which strategy also changes acceptance and rollback behavior?
- Which strategy is currently the default?
- Which strategy is best for fair experiments?
- Which strategy is best for practical repair?

### Required exercise

Fill in this table in your notes:

| Strategy | Prompt source on retry | Rollback target | State carried forward |
|---|---|---|---|
| `original_with_failures` | ? | ? | ? |
| `last_patch_with_failures` | ? | ? | ? |
| `best_patch_with_failures` | ? | ? | ? |

If you cannot fill this table, do not start Phase 2 work yet.

## Step 9: Write Your Own One-Page Explanation

After completing the review, write one page with these headings:

- Entry point
- Main loop
- Data flow
- Artifacts written
- Context strategies
- Failure and rollback behavior
- Open questions

Use plain language. Do not copy from the files.

If you can write that page from memory, you understand the codebase well enough to work on Phase 2.

## Recommended Time Split

- 30 min: `README.md` + `PROJECT_SPEC.md`
- 45 min: `scripts/repair.py` + `loop.py`
- 30 min: support modules
- 30 min: one case + one real run
- 45 min: tests
- 20 min: your one-page summary

## Final Rule

Do not try to understand the whole project at once.

Understand it in this order:

1. Entry point
2. Main loop
3. Support modules
4. Real artifacts
5. Tests
6. Strategy differences

That order matches how the code actually behaves at runtime.
