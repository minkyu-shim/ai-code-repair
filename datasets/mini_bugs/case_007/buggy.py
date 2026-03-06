"""
Layered configuration parsing and rendering helpers.

The config format is INI-like:

    [section]
    extends = parent
    host = db.local
    port = 5432
    dsn = postgres://${host}:${port}

Sections may inherit from one parent section via `extends`. Values may refer
to other keys in the same fully merged section using `${name}` placeholders.
"""

from __future__ import annotations

import re


def parse_config(lines: list[str]) -> dict[str, dict[str, str]]:
    """Parse config lines into a section -> key/value mapping."""
    config: dict[str, dict[str, str]] = {}
    current_section: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].strip()
            config[current_section] = {}
            continue

        if current_section is None:
            raise ValueError("key/value line appeared before any section header")

        key, sep, value = line.partition("=")
        if not sep:
            raise ValueError(f"invalid config line: {raw_line!r}")

        config[current_section][key] = value.strip()

    return config


def referenced_keys(value: str) -> set[str]:
    """Return the placeholder names referenced by a config value."""
    return set(re.findall(r"\$\{([A-Za-z][A-Za-z0-9]*)\}", value))


def merged_section(
    config: dict[str, dict[str, str]],
    name: str,
    _stack: tuple[str, ...] = (),
) -> dict[str, str]:
    """Return one section after recursively applying inheritance."""
    if name in _stack:
        raise ValueError("inheritance cycle detected")

    section = config[name]
    parent_name = section.get("extends")
    parent_values: dict[str, str] = {}

    if parent_name:
        parent_values = merged_section(config, parent_name, _stack + (name,))

    merged = {key: value for key, value in section.items() if key != "extends"}
    merged.update(parent_values)
    return merged


def resolution_order(values: dict[str, str]) -> list[str]:
    """Return the lexicographically smallest valid interpolation order."""
    deps = {
        key: {ref for ref in referenced_keys(value) if ref in values}
        for key, value in values.items()
    }
    indegree = {key: len(refs) for key, refs in deps.items()}
    reverse = {key: set() for key in values}

    for key, refs in deps.items():
        for ref in refs:
            reverse[ref].add(key)

    ready = [key for key, degree in indegree.items() if degree == 0]
    order: list[str] = []

    while ready:
        ready.sort()
        key = ready.pop()
        order.append(key)

        for dependent in sorted(reverse[key]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)

    return order


def _render_value(value: str, env: dict[str, str]) -> str:
    """Substitute `${key}` placeholders using values from `env`."""
    rendered = value
    for ref in referenced_keys(value):
        rendered = rendered.replace(f"${{{ref}}}", env[ref])
    return rendered


def render_section(config: dict[str, dict[str, str]], name: str) -> dict[str, str]:
    """Merge inheritance and resolve placeholders for one section."""
    merged = merged_section(config, name)
    rendered: dict[str, str] = {}

    for key in resolution_order(merged):
        rendered[key] = _render_value(merged[key], merged)

    return rendered


def impacted_sections(
    config: dict[str, dict[str, str]],
    changed: set[str],
) -> set[str]:
    """Return sections that inherit directly or transitively from `changed`."""
    parents = {
        name: values.get("extends")
        for name, values in config.items()
    }
    impacted: set[str] = set()
    stack = list(changed)

    while stack:
        current = stack.pop()
        parent = parents.get(current)
        if parent is None or parent in changed or parent in impacted:
            continue
        impacted.add(parent)
        stack.append(parent)

    return impacted
