import unittest
import os
import sys
from unittest.mock import patch, mock_open, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

import sprint_tools

class TestSprintTools(unittest.TestCase):
    
    @patch('os.listdir')
    def test_list_dir(self, mock_listdir):
        mock_listdir.return_value = ["file1.txt", "file2.txt"]
        result = sprint_tools.list_dir(".")
        self.assertEqual(result, ["file1.txt", "file2.txt"])
        mock_listdir.assert_called_with(".")

    @patch('builtins.open', new_callable=mock_open, read_data="content")
    def test_read_file(self, mock_file):
        result = sprint_tools.read_file("test.txt")
        self.assertEqual(result, "content")
        mock_file.assert_called_with("test.txt", "r", encoding="utf-8")

    @patch('subprocess.run')
    def test_run_command(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = sprint_tools.run_command("echo hello")
        self.assertEqual(result["stdout"], "output")
        self.assertEqual(result["exit_code"], 0)

        result = sprint_tools.run_command("echo hello")
        self.assertEqual(result["stdout"], "output")
        self.assertEqual(result["exit_code"], 0)

    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="def existing_function():\n    pass")
    def test_search_codebase(self, mock_file, mock_walk):
        mock_walk.return_value = [
            ('.', ['subdir'], ['test.py'])
        ]
        
        result = sprint_tools.search_codebase("existing_function")
        self.assertIn("test.py:1: def existing_function():", result)

    @patch('os.walk')
    def test_search_codebase_no_match(self, mock_walk):
        mock_walk.return_value = []
        result = sprint_tools.search_codebase("nonexistent")
        self.assertEqual(result, "No matches found.")

if __name__ == '__main__':
    unittest.main()
