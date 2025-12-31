import unittest
import os
import sys

# Add scripts directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from sprint_config import SprintConfig

class TestSprintConfig(unittest.TestCase):
    def test_defaults(self):
        # We can't easily test env vars here as they are loaded at import time
        # But we can check if keys exist
        self.assertIsNotNone(SprintConfig.CONCURRENCY_LIMIT)
        self.assertIsNotNone(SprintConfig.MODEL_NAME)
    
    def test_role_map(self):
        role_map = SprintConfig.get_role_map()
        self.assertIsInstance(role_map, dict)
        self.assertIn("Backend", role_map)
        self.assertIn("Frontend", role_map)

if __name__ == '__main__':
    unittest.main()
