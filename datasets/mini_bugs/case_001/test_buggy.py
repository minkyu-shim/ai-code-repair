"""
test codes to test buggy.py
"""

from buggy import add


def test_add_basic():
    assert add(2, 3) == 5

def test_add_zero():
    assert add(7, 0) == 7

def test_add_negative():
    assert add(-2, 3)== 1