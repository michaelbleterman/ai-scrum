
import os

def test_ui_content():
    """
    Tests the content of the dummy_ui.txt file.
    """
    file_path = os.path.join(os.path.dirname(__file__), '..', 'project_tracking', 'dummy_ui.txt')
    with open(file_path, 'r') as f:
        content = f.read()
    assert content == "Hello World"
