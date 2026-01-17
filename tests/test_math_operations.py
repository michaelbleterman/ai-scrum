
import sys
import os

# Add the project_tracking directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_tracking.dummy_math import add

def test_addition():
    """
    Tests the add function from dummy_math.
    This test is expected to PASS, confirming the defect is fixed.
    """
    assert add(2, 3) == 5
