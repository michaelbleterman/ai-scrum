
import sys
import os
import pytest

# Add project_tracking to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_tracking.dummy_math import add

def test_add_function_with_bug():
    """
    Tests the add function from dummy_math.py.
    This test is expected to FAIL because of the intentional bug (a - b).
    """
    assert add(2, 3) == 5, "Test failed as expected due to intentional bug."

def test_dummy_ui_content():
    """
    Tests the content of the dummy_ui.txt file.
    This test is expected to PASS.
    """
    file_path = os.path.join(os.path.dirname(__file__), '..', 'project_tracking', 'dummy_ui.txt')
    with open(file_path, 'r') as f:
        content = f.read()
    assert content == "Hello World"
