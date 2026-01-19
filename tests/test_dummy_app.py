import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_tracking import dummy_math

def test_add_intentional_bug():
    """
    This test verifies the correct behavior of the add function.
    The function is expected to return a + b.
    """
    assert dummy_math.add(5, 3) == 8, "Test failed: Expected 5 + 3 = 8"

def test_dummy_ui_content():
    """
    This test verifies the content of the dummy_ui.txt file.
    """
    with open('project_tracking/dummy_ui.txt', 'r') as f:
        content = f.read()
    assert content == "Hello World"
