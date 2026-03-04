"""Smoke test: verify that core modules are importable."""
from __future__ import annotations


def test_repair_loop_importable():
    from ai_code_repair.repair.loop import RepairConfig, RepairLoop

    assert RepairConfig is not None
    assert RepairLoop is not None
