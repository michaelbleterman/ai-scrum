
import unittest
import sys
import os

# Add the project_tracking directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'project_tracking')))

from dummy_math import add

class TestMath(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5, "Should be 5")

if __name__ == '__main__':
    unittest.main()
