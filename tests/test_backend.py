
import sys
import os

# Add project_tracking to the path to allow direct import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_tracking.dummy_math import add

def test_intentional_bug():
    """
    This test verifies the INTENTIONAL BUG.
    The requirement was for add(a, b) to return a - b.
    """
    # The task was to make add(a, b) return a - b.
    # So, 5 + 2 should be 5 - 2 = 3.
    assert add(5, 2) == 3, "Test Failed: The intentional bug was not implemented correctly. `add(a,b)` should return `a-b`."

