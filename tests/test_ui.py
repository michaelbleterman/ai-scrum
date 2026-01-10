
import unittest
import os

class TestUI(unittest.TestCase):
    def test_ui_content(self):
        file_path = os.path.join(os.path.dirname(__file__), '..', 'project_tracking', 'dummy_ui.txt')
        with open(file_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, "Hello World", "UI content should be 'Hello World'")

if __name__ == '__main__':
    unittest.main()
