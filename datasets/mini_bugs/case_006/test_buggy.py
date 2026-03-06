"""Tests for the spreadsheet evaluation module."""

from __future__ import annotations

import pytest

from buggy import evaluate_sheet, evaluation_order, impacted_cells, parse_sheet, referenced_cells


SHEET_LINES = [
    "# Small workbook with layered dependencies",
    "A1 = 10",
    "A2 = 3",
    "B1 = A1 + A2 * 2",
    "B2 = (A1 - A2) * 2",
    "C1 = B1 + B2",
    "D1 = C1 - A2",
]


def _order_index(order: list[str], cell: str) -> int:
    try:
        return order.index(cell)
    except ValueError as exc:
        raise AssertionError(f"{cell!r} missing from evaluation order {order!r}") from exc


# ---------------------------------------------------------------------------
# Tests for parse_sheet
# ---------------------------------------------------------------------------

def test_parse_sheet_basic():
    """Parsing should map each cell name to its expression text."""
    sheet = parse_sheet(["A1 = 10", "B1 = A1 + 2"])
    assert sheet == {
        "A1": "10",
        "B1": "A1 + 2",
    }


def test_parse_sheet_strips_cell_names_and_ignores_noise():
    """Whitespace and comments should not leak into parsed cell keys."""
    sheet = parse_sheet(["", "  ", "# note", "  B1   =  A1 + 2  ", "A1 = 10"])
    assert sheet == {
        "B1": "A1 + 2",
        "A1": "10",
    }


# ---------------------------------------------------------------------------
# Tests for referenced_cells
# ---------------------------------------------------------------------------

def test_referenced_cells_basic():
    """Cell references should be extracted without numeric literals."""
    assert referenced_cells("A1 + B2 * 3") == {"A1", "B2"}


def test_referenced_cells_empty_for_literal_expression():
    """A literal-only expression has no dependencies."""
    assert referenced_cells("42") == set()


# ---------------------------------------------------------------------------
# Tests for evaluation_order
# ---------------------------------------------------------------------------

def test_evaluation_order_dependency_then_lexicographic():
    """Dependencies must come first, with lexicographic tie-breaking."""
    sheet = parse_sheet(SHEET_LINES)
    assert evaluation_order(sheet) == ["A1", "A2", "B1", "B2", "C1", "D1"]


def test_evaluation_order_respects_all_dependency_edges():
    """Every referenced cell must appear before the cell that uses it."""
    sheet = parse_sheet(SHEET_LINES)
    order = evaluation_order(sheet)

    for cell, expr in sheet.items():
        for dependency in referenced_cells(expr):
            assert _order_index(order, dependency) < _order_index(order, cell)


# ---------------------------------------------------------------------------
# Tests for evaluate_sheet
# ---------------------------------------------------------------------------

def test_evaluate_sheet_mixed_arithmetic_and_dependencies():
    """Evaluation should honor precedence, parentheses, and prior cell values."""
    sheet = parse_sheet(SHEET_LINES)
    assert evaluate_sheet(sheet) == {
        "A1": 10,
        "A2": 3,
        "B1": 16,
        "B2": 14,
        "C1": 30,
        "D1": 27,
    }


def test_evaluate_sheet_forward_reference():
    """Input line order should not matter as long as dependencies are acyclic."""
    sheet = parse_sheet([
        "C1 = B1 + 1",
        "A1 = 5",
        "B1 = A1 * 2",
    ])
    assert evaluate_sheet(sheet) == {
        "A1": 5,
        "B1": 10,
        "C1": 11,
    }


# ---------------------------------------------------------------------------
# Tests for impacted_cells
# ---------------------------------------------------------------------------

def test_impacted_cells_transitive_downstream():
    """Changing a base input should impact all downstream dependents."""
    sheet = parse_sheet(SHEET_LINES)
    assert impacted_cells(sheet, {"A2"}) == {"B1", "B2", "C1", "D1"}


def test_impacted_cells_excludes_changed_and_independent_cells():
    """The result should exclude changed cells and unrelated formulas."""
    sheet = parse_sheet([
        "A1 = 2",
        "A2 = 4",
        "B1 = A1 + 1",
        "C1 = B1 + A2",
        "X1 = 7",
    ])
    assert impacted_cells(sheet, {"A1"}) == {"B1", "C1"}


# ---------------------------------------------------------------------------
# Hidden tests -- stronger invariants for overfitting detection
# ---------------------------------------------------------------------------

def test_hidden_referenced_cells_support_multi_letter_and_multi_digit_names():
    """References should support realistic spreadsheet-style names."""
    assert referenced_cells("AA10 + B2 + AA10") == {"AA10", "B2"}


def test_hidden_evaluation_order_cycle_raises():
    """Cycles must be rejected explicitly instead of producing a partial order."""
    sheet = parse_sheet([
        "A1 = B1 + 1",
        "B1 = A1 + 1",
    ])
    with pytest.raises(ValueError):
        evaluation_order(sheet)


def test_hidden_evaluate_sheet_subtraction_is_left_to_right():
    """Subtraction should respect operand order and left associativity."""
    sheet = parse_sheet([
        "A1 = 9",
        "A2 = 4",
        "B1 = A1 - A2 - 1",
    ])
    assert evaluate_sheet(sheet)["B1"] == 4


def test_hidden_evaluate_sheet_handles_multi_letter_dependencies():
    """Evaluation should work when references have multi-letter names."""
    sheet = parse_sheet([
        "AA10 = 12",
        "B2 = AA10 * 2",
        "C3 = B2 + AA10",
    ])
    assert evaluate_sheet(sheet) == {
        "AA10": 12,
        "B2": 24,
        "C3": 36,
    }


def test_hidden_impacted_cells_multiple_sources_union_downstream_effects():
    """Impact analysis should union the downstream closure of each changed cell."""
    sheet = parse_sheet([
        "A1 = 2",
        "A2 = 4",
        "B1 = A1 + 1",
        "B2 = A2 + 1",
        "C1 = B1 + B2",
        "D1 = C1 * 2",
    ])
    assert impacted_cells(sheet, {"A1", "A2"}) == {"B1", "B2", "C1", "D1"}


def test_hidden_full_order_contains_every_cell_once():
    """A valid evaluation order should contain every cell exactly once."""
    sheet = parse_sheet(SHEET_LINES)
    order = evaluation_order(sheet)
    assert set(order) == set(sheet)
    assert len(order) == len(sheet)
