
import sys
import os

# Add project_tracking to the path to allow direct import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_tracking.dummy_math import add

def test_dummy_math_logic():
    """
    Tests the add function from dummy_math.py.
    This is expected to FAIL because of the intentional bug (a - b).
    """
    assert add(5, 5) == 10

def test_dummy_ui_content():
    """
    Tests the content of the dummy_ui.txt file.
    This is expected to PASS.
    """
    ui_path = os.path.join(os.path.dirname(__file__), '..', 'project_tracking', 'dummy_ui.txt')
    with open(ui_path, 'r') as f:
        content = f.read()
    assert content == "Hello World"
