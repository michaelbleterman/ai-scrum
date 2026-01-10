
import sys
import os
import pytest

# Add the project_tracking directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_tracking.dummy_math import add

def test_add_intentional_bug():
    """
    This test is designed to find the intentional bug in the add function.
    The function returns a - b instead of a + b.
    """
    assert add(2, 3) == 5, "Test failed: Expected 2 + 3 = 5"

