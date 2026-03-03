# AI-Assisted Program Repair Using LLMs
Test-Guided, Iterative, Multi-Model Repair Framework

Author: Minkyu SHIM
Institution: EPITA – Computer Science
Project Type: Research + Engineering Framework
Duration: 6–12 months

## 1. Project Overview

### 1.1 Problem Statement

Modern software systems frequently contain defects discovered through failing test cases. Debugging is:

- Time-consuming
- Dependent on developer expertise
- Expensive for companies
- Difficult to scale

Large Language Models (LLMs) such as GPT-class models, Claude, etc., demonstrate strong code generation capabilities. However:

- Generated patches often overfit failing tests
- They may pass tests but violate semantic correctness
- They lack systematic evaluation
- Stability across runs is unknown
- Multi-iteration repair behavior is poorly studied

### 1.2 Core Research Question

**Research Question:** Are LLM-generated patches reliable, generalizable, and stable when integrated into a structured test-driven repair loop?

### 1.3 Hypothesis

A structured repair loop that integrates:

- Test feedback
- Patch validation
- Multi-model comparison
- Iterative correction
- Overfitting detection

will significantly improve:

- Patch correctness
- Stability
- Generalization

compared to naive one-shot prompting.

## 2. Objectives

### 2.1 Scientific Objectives

- Measure patch reliability
- Measure semantic correctness
- Detect test overfitting
- Compare multiple LLMs quantitatively
- Analyze iterative repair convergence behavior
- Evaluate stability across repeated runs

### 2.2 Engineering Objectives

Build a modular framework that:

- Accepts buggy programs
- Executes tests automatically
- Calls LLM APIs
- Applies patches
- Validates results
- Logs structured evaluation metrics
- Supports multi-model benchmarking

This should be production-quality code suitable for a research portfolio.

## 3. System Architecture

### 3.1 High-Level Architecture

```
Buggy Code
    ↓
Test Runner
    ↓
Failure Report
    ↓
LLM Patch Generator
    ↓
Patch Application
    ↓
Re-run Tests
    ↓
Evaluation & Logging
    ↓
Repeat Loop (if needed)
```

### 3.2 Core Modules

### 1️⃣ Runner

**Responsibilities:**

- Execute pytest
- Generate JUnit XML
- Parse results
- Return structured summary

**Output:**

```python
class PytestSummary:
    tests: int
    failures: int
    errors: int
    skipped: int
    passed: int
```

### 2️⃣ Patch Generator

**Responsibilities:**

- Send structured prompt to LLM
- Provide:
  - Failing test output
  - Buggy source code
  - Constraints
- Receive candidate patch
- Must support:
  - GPT models
  - Claude
  - Future models

### 3️⃣ Patch Applier

**Responsibilities:**

- Safely apply patch
- Preserve original copy
- Support rollback
- Validate syntax

### 4️⃣ Evaluation Engine

**Responsibilities:**

- Compute:
  - Pass rate improvement
  - Compilation success
  - Runtime errors
  - Stability metrics
- Detect overfitting

### 5️⃣ Experiment Logger

**Responsibilities:**

- Store:
  - Model name
  - Prompt version
  - Iteration number
  - Patch content
  - Test results
  - Time taken
- Export CSV/JSON for statistical analysis

## 4. Research Phases

### Phase 1 — Minimal Repair Loop (Foundation)

**Goal:** Build a working single-model repair loop.

**Tasks:**

- Implement runner.py
- Implement JUnit XML parsing
- Implement patch application
- Implement single LLM call
- Create basic loop:
  - Run tests
  - If failing → ask LLM
  - Apply patch
  - Re-run tests
  - Log iteration results

**Deliverable:** Working MVP capable of repairing small Python bugs.

### Phase 2 — Iterative Repair Framework

**Goal:** Introduce structured iteration control.

**Add:**

- Max iteration threshold
- Early stopping
- Temperature control
- Deterministic vs stochastic runs
- Retry strategy

**Research Question:** Does iterative repair improve final correctness?

### Phase 3 — Overfitting Detection

**Goal:** Detect patches that pass tests but are semantically wrong.

**Strategies:**

- Hidden test cases
- Mutation testing
- Test amplification
- Random input generation
- Cross-validation

**Metrics:**

- Test Pass Rate
- Generalization Score
- Overfitting Rate

### Phase 4 — Multi-Model Benchmarking

**Goal:** Compare models under identical conditions.

**Variables:**

- Model type
- Prompt structure
- Iteration limit
- Temperature
- Context length

**Metrics:**

| Metric | Description |
|---|---|
| Success Rate | % fully repaired |
| Partial Fix Rate | % improved but not full |
| Overfitting Rate | False positives |
| Stability Score | Same result across runs |
| Avg Iterations | Repair convergence speed |
| Cost Efficiency | $ per successful fix |

### Phase 5 — Stability Analysis

**Goal:** Test reproducibility.

Run same bug:

- 10 times per model

Measure:

- Patch similarity
- Success consistency
- Variance

### Phase 6 — Dataset Scaling

**Use:**

- Small curated mini-bugs
- Larger bug benchmarks
- Custom synthetic bugs

Evaluate scalability and cost.

## 5. Experimental Design

### 5.1 Independent Variables

- Model type
- Prompt version
- Iteration limit
- Temperature
- Bug complexity

### 5.2 Dependent Variables

- Repair success
- Iterations required
- Overfitting detection
- Stability
- Runtime
- Cost

## 6. Evaluation Metrics

### 6.1 Repair Success

Success = All tests pass

### 6.2 Improvement Score

Improvement = (Initial failures - Final failures) / Initial failures

### 6.3 Stability

Stability = Successful runs / Total runs

### 6.4 Overfitting Rate

Overfitting = Passed visible tests but failed hidden tests

## 7. Expected Contributions

- Structured LLM repair loop architecture
- Overfitting detection framework
- Multi-model empirical comparison
- Stability measurement methodology
- Dataset and benchmark tooling

## 8. Risks & Mitigation

| Risk | Mitigation |
|---|---|
| LLM always succeeds | Increase difficulty & hidden tests |
| LLM never succeeds | Analyze failure modes |
| High API cost | Use mini datasets |
| Non-reproducible results | Run multiple seeds |
| Overfitting not detectable | Add mutation testing |

## 9. Academic Deliverables

Bachelor Thesis Structure

- Introduction
- Background on Program Repair
- LLMs in Code Generation
- Proposed Framework
- Experimental Setup
- Results
- Analysis
- Limitations
- Future Work

## 10. Engineering Deliverables

- Clean modular repository
- Automated experiment runner
- Config-based experiment execution
- CSV export of results
- README documentation
- Architecture diagrams
- Reproducibility guide

## 11. Long-Term Extension (Master's Level)

- Reinforcement Learning fine-tuning
- Repair ranking models
- Static analysis integration
- Hybrid symbolic + LLM repair
- CI/CD integration prototype
- SaaS version for automated debugging

## 12. Project Timeline (6–12 Months)

| Month | Focus |
|---|---|
| 1–2 | Core loop |
| 3–4 | Iteration & evaluation |
| 5–6 | Multi-model benchmark |
| 7–8 | Stability + scaling |
| 9–10 | Statistical analysis |
| 11–12 | Thesis writing |

## 13. What This Project Is NOT

- Not just a coding project
- Not just comparing APIs
- Not just prompting

It is:

A structured empirical research study on LLM reliability in automated software repair.

## 14. Final Vision

This project should:

- Demonstrate research maturity
- Demonstrate engineering maturity
- Show experimental rigor
- Be suitable for Master's applications
- Potentially evolve into a publishable paper
