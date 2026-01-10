
import pytest
import os

def test_ui_content():
    with open(os.path.join("project_tracking", "dummy_ui.txt"), "r") as f:
        content = f.read()
    assert content == "Hello World"
