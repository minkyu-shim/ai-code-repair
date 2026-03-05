"""Tests for the inventory order processing module."""

from buggy import calculate_total, apply_tax, process_order


# ---------------------------------------------------------------------------
# Tests for calculate_total
# ---------------------------------------------------------------------------

def test_calculate_total_no_discount():
    """Items below the bulk threshold get no discount."""
    items = [("pen", 2.0, 3), ("notebook", 5.0, 2)]
    # 2*3 + 5*2 = 6 + 10 = 16
    assert calculate_total(items) == 16.0


def test_calculate_total_with_discount():
    """Items with quantity >= 5 receive a 10% discount on that line."""
    items = [("pen", 2.0, 5)]
    # 2*5 = 10, 10% off -> 9.0
    assert calculate_total(items) == 9.0


def test_calculate_total_exact_threshold():
    """Quantity of exactly 5 should trigger the bulk discount."""
    items = [("widget", 10.0, 5)]
    # 10*5 = 50, 10% off -> 45.0
    assert calculate_total(items) == 45.0


def test_calculate_total_mixed():
    """Mix of discounted and non-discounted items."""
    items = [
        ("apple", 1.50, 10),  # 15.0 * 0.9 = 13.50
        ("banana", 0.75, 3),  # 2.25, no discount
    ]
    assert calculate_total(items) == 15.75


def test_calculate_total_empty():
    """An empty order has zero total."""
    assert calculate_total([]) == 0.0


# ---------------------------------------------------------------------------
# Tests for apply_tax
# ---------------------------------------------------------------------------

def test_apply_tax_standard():
    """Standard 8% tax on 100."""
    assert apply_tax(100.0, 0.08) == 108.0


def test_apply_tax_zero_rate():
    """Zero tax rate returns the subtotal unchanged."""
    assert apply_tax(50.0, 0.0) == 50.0


def test_apply_tax_zero_subtotal():
    """Zero subtotal with any tax rate is still zero."""
    assert apply_tax(0.0, 0.1) == 0.0


def test_apply_tax_rounding():
    """Result should be rounded to 2 decimal places."""
    # 33.33 * 1.07 = 35.6631 -> 35.66
    assert apply_tax(33.33, 0.07) == 35.66


# ---------------------------------------------------------------------------
# Tests for process_order
# ---------------------------------------------------------------------------

def test_process_order_basic():
    """Full order processing with discount and tax."""
    items = [("widget", 10.0, 5)]
    result = process_order(items, 0.1)
    # subtotal: 10*5=50, discount -> 45.0
    # tax: 45.0 * 0.1 = 4.5
    # total: 45.0 * 1.1 = 49.5
    assert result["subtotal"] == 45.0
    assert result["tax"] == 4.5
    assert result["total"] == 49.5


def test_process_order_no_discount():
    """Order where no items hit the bulk threshold."""
    items = [("pen", 3.0, 2), ("eraser", 1.0, 4)]
    result = process_order(items, 0.05)
    # subtotal: 6 + 4 = 10.0 (no discount)
    # tax: 10.0 * 0.05 = 0.5
    # total: 10.0 * 1.05 = 10.5
    assert result["subtotal"] == 10.0
    assert result["tax"] == 0.5
    assert result["total"] == 10.5


def test_process_order_consistency():
    """The tax field must equal total - subtotal."""
    items = [("bolt", 0.50, 20)]
    result = process_order(items, 0.08)
    assert abs(result["tax"] - (result["total"] - result["subtotal"])) < 0.01


# ---------------------------------------------------------------------------
# Hidden tests — stricter invariants for overfitting detection (Phase 3)
# ---------------------------------------------------------------------------

def test_hidden_discount_boundary():
    """Quantity 4 must NOT get discount, quantity 5 MUST get discount."""
    no_discount = [("x", 20.0, 4)]
    with_discount = [("x", 20.0, 5)]
    assert calculate_total(no_discount) == 80.0   # 20*4, no discount
    assert calculate_total(with_discount) == 90.0  # 20*5=100, 10% off -> 90


def test_hidden_tax_proportional():
    """Tax must scale proportionally with subtotal — not be a fixed offset."""
    tax_on_100 = apply_tax(100.0, 0.1) - 100.0   # should be 10.0
    tax_on_200 = apply_tax(200.0, 0.1) - 200.0   # should be 20.0
    assert abs(tax_on_200 - 2 * tax_on_100) < 0.01
