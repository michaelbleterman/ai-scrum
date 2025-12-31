import unittest
import os
import sys
from unittest.mock import patch, mock_open

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

import sprint_utils

class TestSprintUtils(unittest.TestCase):
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_detect_latest_sprint_file(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        mock_listdir.return_value = ["SPRINT_1.md", "SPRINT_2.md", "other.txt"]
        
        result = sprint_utils.detect_latest_sprint_file("dummy_dir")
        self.assertTrue(result.endswith("SPRINT_2.md"))
        
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="### @Backend\n- [ ] Task 1\n- [x] Task 2\n### @Frontend\n- [ ] Task 3")
    def test_parse_sprint_tasks(self, mock_file, mock_exists):
        mock_exists.return_value = True
        tasks = sprint_utils.parse_sprint_tasks("SPRINT_X.md")
        
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]['role'], 'Backend')
        self.assertEqual(tasks[0]['desc'], 'Task 1')
        self.assertEqual(tasks[1]['role'], 'Frontend')
        self.assertEqual(tasks[1]['desc'], 'Task 3')

if __name__ == '__main__':
    unittest.main()
