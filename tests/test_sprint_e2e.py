
import unittest
import sys
import os

# Add project_tracking to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_tracking.dummy_math import add

class TestSprintE2E(unittest.TestCase):

    def test_add_function_correctness(self):
        """
        Tests if the 'add' function in dummy_math.py performs addition correctly.
        This verifies the fix for the defect.
        """
        self.assertEqual(add(2, 3), 5, "The 'add' function should return a + b")

    def test_dummy_ui_content(self):
        """
        Tests if the dummy_ui.txt file contains the correct 'Hello World' text.
        """
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'project_tracking', 'dummy_ui.txt')
        with open(ui_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, "Hello World", "The content of dummy_ui.txt should be 'Hello World'")

if __name__ == '__main__':
    unittest.main()
