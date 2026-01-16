
import sys
import os

# This is a common pattern to ensure the test runner can find the module to test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_tracking.dummy_math import add

def test_add_bug_confirmation():
    """
    This test is designed to fail, confirming the defect that add(a, b)
    is incorrectly implemented as a - b.
    """
    expected_result = 5
    actual_result = add(2, 3)
    assert actual_result == expected_result, f"DEFECT CONFIRMED: Expected 2 + 3 to be {expected_result}, but got {actual_result}."
