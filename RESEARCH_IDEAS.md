# Research Ideas & Open Questions

This file tracks research topics that emerged during development for future investigation.

---

## [RQ-001] Iteration Context Strategy: What Should the LLM See on Retry?

**Status:** Open — not yet implemented or tested
**Priority:** High (potential thesis contribution)
**Relevant phase:** Phase 2 (Iterative Repair) / Phase 4 (Multi-Model Benchmarking)

### The Question

When the LLM's patch fails and the loop retries, what source code and test feedback should be included in the next prompt?

### The Three Options

| Option | Source code shown | Test failures shown | Key risk |
|---|---|---|---|
| **A — Always original** | Original buggy file | From the previous failed patch | Prompt incoherence; LLM doesn't know what it already tried → may repeat same patch |
| **B — Show failed patch** | LLM's last attempt | From that failed patch | Structural drift; compounding errors over iterations |
| **C — Show both** | Original + last patch | From the failed patch | Token cost; attention dilution |

### Proposed Best Design: Anchored Incremental Context (Hybrid)

Show:
1. **Original buggy code** as the authoritative anchor (always, never changes)
2. **Diff of the last failed patch** (not the full file — just what changed)
3. **Test failures from that failed patch**
4. Explicit instruction: *"Start from the original. Use the last attempt only to understand what not to do."*

This gives the LLM negative signal (what it already tried) without risking drift from the original intent.

### Why This Is Research-Worthy

Connects to active LLM literature on self-refinement. Huang et al. (2023) showed LLMs struggle to genuinely self-correct without external feedback. This experiment would produce empirical data on that question in the specific domain of program repair.

**Core research question:**
> *Do LLMs self-correct better when shown their own failed output, or when anchored to the original with negative signal about what didn't work?*

### Experimental Design

| Variable | Levels |
|---|---|
| Context strategy | A (original only), B (failed patch), Hybrid (original + diff) |
| Model | All tested models |
| Max iterations | 3, 5, 10 |
| Bug difficulty | Easy, medium, hard |

**Metrics to compare:**
- Success rate per iteration (convergence curve)
- Final success rate
- Overfitting rate (passes visible tests but fails hidden tests)
- Edit distance from original (drift measurement)
- Patch repetition rate (did the LLM try the same fix twice?)
- Stability across repeated runs

### Current Framework Status

The current implementation uses **a variant of Option A with an inconsistency**: source code shown is the original (restored from snapshot), but test failures come from the previous failed patch. This is the baseline to compare against.

### Action Items

- [ ] Lock in Option A as stable baseline before experimenting
- [ ] Implement context strategy as a configurable parameter in `RepairConfig`
- [ ] Design hidden test suite for overfitting detection (needed for this study)
- [ ] Run A vs B vs Hybrid across at least 2 models, 3 iteration limits
