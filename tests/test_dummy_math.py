# tests/test_dummy_math.py
from project_tracking.dummy_math import add

def test_add_positive_numbers():
    """
    Tests that the add function correctly sums two positive integers.
    """
    assert add(2, 3) == 5

def test_add_negative_numbers():
    """
    Tests that the add function correctly sums two negative integers.
    """
    assert add(-2, -3) == -5

def test_add_mixed_numbers():
    """
    Tests that the add function correctly sums a positive and a negative integer.
    """
    assert add(5, -3) == 2
