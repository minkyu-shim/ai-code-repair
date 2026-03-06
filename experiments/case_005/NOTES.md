# case_005 — Experiment Notes

## Bug Summary

case_005 is a dependency-planning module (`buggy.py`, 96 LOC, 16 tests: 9 visible + 7 hidden). It has 5 bugs across 4 functions:

1. `parse_rules` — missing leaf-node registration: dependencies that only appear on the right-hand side of rules are never added as graph keys. Also, target names are not stripped of whitespace.
2. `build_order` — wrong ready-node selection: `ready.pop()` takes the last (lexicographically largest) element; should be `ready.pop(0)` for lex-smallest.
3. `build_order` — missing cycle detection: no `ValueError` raised when the graph contains a cycle.
4. `parallel_stages` — stage frontier leak: merges current-stage nodes with next-stage newly-unlocked nodes into one stage instead of appending only the current stage.
5. `affected_by_change` — wrong traversal direction: traverses `graph[node]` (upstream dependencies) instead of the reverse graph (downstream dependents).

## Run Log (one entry per run_id)

### Run: `20260305T215059Z`

- Model: `gemini-2.5-flash`
- Context strategy: `original_with_failures` (Strategy A)
- Max iterations: 3
- Outcome: FAILED (15/16 at best)
- Total wall time: 121.6s

| Iteration | Passed/Total | Notes |
|---|---|---|
| Baseline | 3/16 | 13 tests failing |
| 1 | 15/16 | LLM fixed all 5 bugs; improvement score 92.3% |
| 2 | 13/16 | Regression: Strategy A reset to original; model focused on 1 remaining failure and lost 2 previously fixed bugs |
| 3 | 15/16 | Recovered; stalled at same plateau |

## Key Findings

1. **One-shot pattern broken** — First case that Gemini 2.5 Flash could not fully repair. Validates harder case design. `expected_min_iterations: 4` was not met in 3 iterations.
2. **Strategy A regression observed in the wild** — Iteration 2 is a textbook demonstration: shown only 1 failing test against the original buggy code, the model focused narrowly and dropped 4 previously correct fixes. Net result: 15/16 → 13/16. Direct empirical evidence for RQ-001.
3. **Convergence plateau** — Iterations 1 and 3 both reached 15/16 and stalled on the same test. The model cannot self-correct past this point without external guidance.
4. **Possible test expectation inconsistency** — `test_build_order_dependency_first` may have a wrong expected output. The LLM's output (`parse, lint, scan, ...`) is the correct lexicographically-smallest topological order. The test expects `parse, scan, compile, lint, ...` which corresponds to BFS-level-order (process all nodes at current depth before moving deeper), not lex-smallest. No repair agent can pass this test without matching an unstated assumption.

## Open Questions / Action Items

1. Verify `test_build_order_dependency_first` expectation — trace the expected output against Kahn's algorithm with lex-smallest tie-breaking. Fix the test if the expectation is wrong; clarify the docstring if the intended semantics differ from lex-smallest.
2. Re-run with `--context-strategy last_patch_with_failures` (Strategy B) — the iteration 2 regression makes this the ideal A/B comparison case.
3. Increase `--max-iterations` to at least 5 (meta says `expected_min_iterations: 4`; this run used only 3).
4. Run 5+ repetitions with both strategies to measure stability of the 15/16 plateau and strategy A vs B divergence.
5. Consider adding `stall_iteration` as a tracked metric — the first iteration where improvement stops.
