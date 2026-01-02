import os

def test_dummy_ui_content():
    """
    Tests if the dummy_ui.txt file contains the expected text.
    """
    file_path = os.path.join("project_tracking", "dummy_ui.txt")
    with open(file_path, "r") as f:
        content = f.read()
    assert content == "Hello World"
