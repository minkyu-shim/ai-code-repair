"""
Inventory order processing module.

Provides functions to calculate order totals with bulk discounts,
apply tax, and process complete orders.

Bulk discount rule: 10% off any line item where quantity >= 5.
"""

from __future__ import annotations


def calculate_total(items: list[tuple[str, float, int]]) -> float:
    """Calculate the total cost of items with bulk discount.

    Each item is a (name, price, quantity) tuple.
    A 10% discount is applied to any line item where quantity >= 5.

    Returns the total rounded to 2 decimal places.
    """
    total = 0.0
    for name, price, quantity in items:
        line_cost = price * quantity
        if quantity >= 5:  # Changed from '>' to '>=' to include quantity of 5 for discount
            line_cost *= 0.9
        total += line_cost
    return round(total, 2)


def apply_tax(subtotal: float, tax_rate: float) -> float:
    """Apply tax to a subtotal and return the grand total.

    tax_rate is expressed as a decimal (e.g., 0.08 for 8%).
    Returns the result rounded to 2 decimal places.
    """
    # Tax should be calculated as subtotal * (1 + tax_rate)
    return round(subtotal * (1 + tax_rate), 2)


def process_order(
    items: list[tuple[str, float, int]], tax_rate: float
) -> dict[str, float]:
    """Process a complete order.

    Computes the discounted subtotal, tax amount, and grand total.
    Returns a dict with keys: "subtotal", "tax", "total".
    """
    subtotal = calculate_total(items)
    total = apply_tax(subtotal, tax_rate)
    # Tax should be calculated based on the discounted subtotal
    tax = total - subtotal
    return {
        "subtotal": subtotal,
        "tax": round(tax, 2),
        "total": total,
    }

