
import sys
import os

# Add project_tracking to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_tracking.dummy_math import add

def test_add():
    """
    Tests the add function from dummy_math.
    This test is expected to fail due to the intentional bug.
    """
    assert add(2, 3) == 5
