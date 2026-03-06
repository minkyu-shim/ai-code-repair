"""
Spreadsheet parsing and evaluation helpers.

Each input line uses the form "CELL = expression" where expressions may contain
integer literals, cell references, parentheses, and the operators +, -, and *.
"""

from __future__ import annotations

import re

_OPS = {"+": 1, "-": 1, "*": 2}


def parse_sheet(lines: list[str]) -> dict[str, str]:
    """Parse spreadsheet definitions from text lines."""
    sheet: dict[str, str] = {}

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        cell, _, expr = line.partition("=")
        sheet[cell] = expr.strip()

    return sheet


def referenced_cells(expr: str) -> set[str]:
    """Return the set of cell references used inside an expression."""
    return set(re.findall(r"[A-Z][0-9]", expr))


def _indexes(sheet: dict[str, str]) -> tuple[dict[str, set[str]], dict[str, int], dict[str, set[str]]]:
    """Build dependency, indegree, and reverse-edge indexes."""
    graph = {cell: referenced_cells(expr) for cell, expr in sheet.items()}
    indegree = {cell: 0 for cell in graph}
    reverse = {cell: set() for cell in graph}

    for cell, deps in graph.items():
        for dep in deps:
            indegree[cell] += 1
            reverse.setdefault(dep, set()).add(cell)

    return graph, indegree, reverse


def evaluation_order(sheet: dict[str, str]) -> list[str]:
    """Return the lexicographically smallest valid evaluation order."""
    _, indegree, reverse = _indexes(sheet)
    ready = [cell for cell, degree in indegree.items() if degree == 0]
    order: list[str] = []

    while ready:
        ready.sort()
        cell = ready.pop()
        order.append(cell)

        for dependent in sorted(reverse.get(cell, set())):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)

    return order


def _tokenize(expr: str) -> list[str]:
    """Split an expression into tokens."""
    tokens: list[str] = []
    current = ""

    for char in expr.replace(" ", ""):
        if char in _OPS or char in "()":
            if current:
                tokens.append(current)
                current = ""
            tokens.append(char)
        else:
            current += char

    if current:
        tokens.append(current)

    return tokens


def _to_postfix(tokens: list[str]) -> list[str]:
    """Convert infix tokens to postfix form."""
    output: list[str] = []
    stack: list[str] = []

    for token in tokens:
        if token in _OPS:
            while stack and stack[-1] != "(" and _OPS[stack[-1]] <= _OPS[token]:
                output.append(stack.pop())
            stack.append(token)
        elif token == "(":
            stack.append(token)
        elif token == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if stack and stack[-1] == "(":
                stack.pop()
        else:
            output.append(token)

    while stack:
        output.append(stack.pop())

    return output


def _value(token: str, env: dict[str, int]) -> int:
    if token.isdigit():
        return int(token)
    return env[token]


def _eval_postfix(tokens: list[str], env: dict[str, int]) -> int:
    """Evaluate a postfix expression using already-computed cell values."""
    stack: list[int] = []

    for token in tokens:
        if token in _OPS:
            right = stack.pop()
            left = stack.pop()

            if token == "+":
                stack.append(left + right)
            elif token == "-":
                stack.append(right - left)
            else:
                stack.append(left * right)
        else:
            stack.append(_value(token, env))

    return stack[-1]


def evaluate_sheet(sheet: dict[str, str]) -> dict[str, int]:
    """Evaluate every cell in dependency order."""
    values: dict[str, int] = {}

    for cell in evaluation_order(sheet):
        postfix = _to_postfix(_tokenize(sheet[cell]))
        values[cell] = _eval_postfix(postfix, values)

    return values


def impacted_cells(sheet: dict[str, str], changed: set[str]) -> set[str]:
    """Return all cells whose value depends on any changed cell."""
    graph, _, _ = _indexes(sheet)
    impacted: set[str] = set()
    stack = list(changed)

    while stack:
        cell = stack.pop()
        for dependency in graph.get(cell, set()):
            if dependency in changed or dependency in impacted:
                continue
            impacted.add(dependency)
            stack.append(dependency)

    return impacted
