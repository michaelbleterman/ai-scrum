import os
from project_tracking.dummy_math import add

def test_add_function():
    # Expecting 2 + 3 = 5
    result = add(2, 3)
    assert result == 5, f"Expected 5, but got {result}"

def test_ui_content():
    ui_path = "project_tracking/dummy_ui.txt"
    assert os.path.exists(ui_path), "UI file does not exist"
    with open(ui_path, "r") as f:
        content = f.read().strip()
    assert content == "UI Loaded", f"Expected 'UI Loaded', but got '{content}'"
