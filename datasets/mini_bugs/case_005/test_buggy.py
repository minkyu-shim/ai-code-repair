"""Tests for the dependency planning module."""

from __future__ import annotations

import pytest

from buggy import affected_by_change, build_order, parallel_stages, parse_rules


RULES = [
    "package: test deploy",
    "deploy: build",
    "test: build lint",
    "build: compile",
    "lint: parse",
    "compile: parse scan",
    "parse:",
    "scan:",
]


def _stage_index(stages: list[list[str]], node: str) -> int:
    for index, stage in enumerate(stages):
        if node in stage:
            return index
    raise AssertionError(f"node {node!r} not found in any stage")


# ---------------------------------------------------------------------------
# Tests for parse_rules
# ---------------------------------------------------------------------------

def test_parse_rules_explicit_empty_target():
    """Targets written as `name:` should parse as empty dependency sets."""
    assert parse_rules(["parse:"]) == {"parse": set()}


def test_parse_rules_adds_leaf_only_dependencies():
    """Dependencies that never appear on the left must still become graph nodes."""
    assert parse_rules(["build: parse scan", "parse:"]) == {
        "build": {"parse", "scan"},
        "parse": set(),
        "scan": set(),
    }


def test_parse_rules_ignores_blank_and_comment_lines():
    """Blank lines and comments should not produce nodes."""
    graph = parse_rules(["", "   ", "# ignore me", "build: parse", "parse:"])
    assert graph == {
        "build": {"parse"},
        "parse": set(),
    }


# ---------------------------------------------------------------------------
# Tests for build_order
# ---------------------------------------------------------------------------

def test_build_order_dependency_first():
    """A valid build order must place every dependency before its dependents."""
    graph = parse_rules(RULES)
    assert build_order(graph) == [
        "parse",
        "scan",
        "compile",
        "lint",
        "build",
        "deploy",
        "test",
        "package",
    ]


def test_build_order_lexicographic_tie_break():
    """When several nodes are ready, the lexicographically smallest goes first."""
    graph = {
        "package": {"deploy", "test"},
        "deploy": set(),
        "test": set(),
    }
    assert build_order(graph) == ["deploy", "test", "package"]


# ---------------------------------------------------------------------------
# Tests for parallel_stages
# ---------------------------------------------------------------------------

def test_parallel_stages_group_independent_work():
    """Independent nodes should share a stage until later dependencies unlock."""
    graph = parse_rules(RULES)
    assert parallel_stages(graph) == [
        ["parse", "scan"],
        ["compile", "lint"],
        ["build"],
        ["deploy", "test"],
        ["package"],
    ]


def test_parallel_stages_chain_has_one_task_per_stage():
    """A linear dependency chain should yield one task in each stage."""
    graph = {
        "package": {"build"},
        "build": {"compile"},
        "compile": {"parse"},
        "parse": set(),
    }
    assert parallel_stages(graph) == [
        ["parse"],
        ["compile"],
        ["build"],
        ["package"],
    ]


# ---------------------------------------------------------------------------
# Tests for affected_by_change
# ---------------------------------------------------------------------------

def test_affected_by_change_returns_transitive_dependents():
    """A change should impact every downstream target, not its prerequisites."""
    graph = parse_rules(RULES)
    assert affected_by_change(graph, {"parse"}) == {
        "compile",
        "lint",
        "build",
        "deploy",
        "test",
        "package",
    }


def test_affected_by_change_excludes_changed_targets():
    """Changed nodes themselves are not included in the downstream result set."""
    graph = parse_rules(RULES)
    assert affected_by_change(graph, {"parse", "scan"}) == {
        "compile",
        "lint",
        "build",
        "deploy",
        "test",
        "package",
    }


# ---------------------------------------------------------------------------
# Hidden tests -- stronger invariants for overfitting detection
# ---------------------------------------------------------------------------

def test_hidden_parse_rules_strips_whitespace():
    """Whitespace around a target name should not leak into the graph key."""
    graph = parse_rules(["  build  : parse scan  ", "parse:", "scan:"])
    assert graph["build"] == {"parse", "scan"}


def test_hidden_parse_rules_deduplicates_dependencies():
    """Repeated dependencies should collapse to a single edge."""
    graph = parse_rules(["build: parse scan parse", "parse:", "scan:"])
    assert graph["build"] == {"parse", "scan"}


def test_hidden_build_order_cycle_raises():
    """Cycles are invalid and should be rejected explicitly."""
    graph = {
        "compile": {"parse"},
        "parse": {"compile"},
    }
    with pytest.raises(ValueError):
        build_order(graph)


def test_hidden_parallel_stages_never_repeat_nodes():
    """Each node should appear in exactly one parallel stage."""
    graph = parse_rules(RULES)
    stages = parallel_stages(graph)
    flattened = [node for stage in stages for node in stage]
    assert len(flattened) == len(set(flattened))
    assert set(flattened) == set(graph)


def test_hidden_parallel_stages_respect_dependency_levels():
    """Dependencies must always appear in an earlier stage than their target."""
    graph = parse_rules(RULES)
    stages = parallel_stages(graph)

    for node, deps in graph.items():
        for dep in deps:
            assert _stage_index(stages, dep) < _stage_index(stages, node)


def test_hidden_affected_by_change_with_multiple_sources():
    """Multiple changed inputs should union their downstream impact."""
    graph = parse_rules(RULES)
    assert affected_by_change(graph, {"lint", "scan"}) == {
        "compile",
        "build",
        "deploy",
        "test",
        "package",
    }


def test_hidden_affected_by_change_leaf_with_no_dependents():
    """A terminal target with no downstream dependents should affect nothing."""
    graph = parse_rules(RULES)
    assert affected_by_change(graph, {"package"}) == set()
