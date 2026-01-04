
import sys
import os

# Add project_tracking to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_tracking.dummy_math import add

def test_add_function():
    assert add(2, 3) == 5

def test_ui_file_content():
    with open('project_tracking/dummy_ui.txt', 'r') as f:
        content = f.read()
    assert content == "UI Loaded"
