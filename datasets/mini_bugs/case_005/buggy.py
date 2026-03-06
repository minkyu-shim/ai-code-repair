"""
Dependency planning utilities for small build graphs.

Each rule uses the form "target: dep1 dep2 dep3". The parsed graph maps each
target to the set of targets that must be completed before that target can run.
"""

from __future__ import annotations


def parse_rules(lines: list[str]) -> dict[str, set[str]]:
    """Parse dependency rules from text lines.

    Blank lines and comment lines beginning with "#" are ignored. Targets with
    no dependencies are written as "name:".
    """
    graph: dict[str, set[str]] = {}

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        target, _, remainder = line.partition(":")
        deps = set(remainder.split())
        graph[target] = deps

    return graph


def _indexes(graph: dict[str, set[str]]) -> tuple[dict[str, int], dict[str, set[str]]]:
    """Build indegree and reverse-edge indexes for the dependency graph."""
    indegree = {node: 0 for node in graph}
    reverse = {node: set() for node in graph}

    for node, deps in graph.items():
        for dep in deps:
            indegree[node] += 1
            reverse[dep].add(node)

    return indegree, reverse


def build_order(graph: dict[str, set[str]]) -> list[str]:
    """Return the lexicographically smallest valid topological build order.

    Raises ValueError if the graph contains a cycle.
    """
    indegree, reverse = _indexes(graph)
    ready = [node for node, degree in indegree.items() if degree == 0]
    order: list[str] = []

    while ready:
        ready.sort()
        node = ready.pop()
        order.append(node)

        for dependent in sorted(reverse[node]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)

    return order


def parallel_stages(graph: dict[str, set[str]]) -> list[list[str]]:
    """Split the build into dependency-respecting parallel stages.

    Each stage contains tasks that can run together once all earlier stages are
    complete. Tasks inside a stage are returned in lexicographic order.
    """
    indegree, reverse = _indexes(graph)
    ready = sorted(node for node, degree in indegree.items() if degree == 0)
    stages: list[list[str]] = []

    while ready:
        next_ready: list[str] = []

        for node in ready:
            for dependent in sorted(reverse[node]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    next_ready.append(dependent)

        stages.append(sorted(ready + next_ready))
        ready = sorted(next_ready)

    return stages


def affected_by_change(
    graph: dict[str, set[str]], changed: set[str]
) -> set[str]:
    """Return all targets that depend directly or transitively on `changed`.

    The changed targets themselves are not included in the result.
    """
    affected: set[str] = set()
    stack = list(changed)

    while stack:
        node = stack.pop()
        for dep in graph.get(node, set()):
            if dep in changed or dep in affected:
                continue
            affected.add(dep)
            stack.append(dep)

    return affected
