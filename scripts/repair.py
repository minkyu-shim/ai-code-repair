#!/usr/bin/env python3
"""
AI Code Repair — Phase 1 CLI.

Usage:
    python scripts/repair.py --case datasets/mini_bugs/case_001
    python scripts/repair.py --case datasets/mini_bugs/case_002 --max-iterations 3
"""
import argparse
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from ai_code_repair.repair import ContextStrategy, RepairConfig, RepairLoop


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Code Repair - Phase 1")
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--max-iterations", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--context-strategy",
        choices=[s.value for s in ContextStrategy],
        default=ContextStrategy.ORIGINAL_WITH_FAILURES.value,
        help="Context strategy for retry iterations (default: original_with_failures)",
    )
    args = parser.parse_args()

    config = RepairConfig(
        case_dir=args.case,
        max_iterations=args.max_iterations,
        timeout_seconds=args.timeout,
        context_strategy=ContextStrategy(args.context_strategy),
    )
    result = RepairLoop(config).run()

    if result.success:
        status = "[REPAIRED]" if result.total_iterations > 0 else "[ALREADY PASSING]"
    else:
        status = "[FAILED]"

    print(f"{status} {args.case} — {result.total_iterations} iteration(s)")
    print("Result saved to experiments/")


if __name__ == "__main__":
    main()
