"""
test codes to test buggy.py
"""

from buggy import add, subtract


def test_add_basic():
    assert add(2, 3) == 5

def test_add_zero():
    assert add(7, 0) == 7

def test_add_negative():
    assert add(-2, 3)== 1

def test_subtract_basic():
    assert subtract(3, 1) == 2

def test_subtract_zero():
    assert subtract(5, 0) == 5

def test_subtract_negative():
    assert subtract(4, -9) == 13