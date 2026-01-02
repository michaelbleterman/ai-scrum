import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import os
import sys

# Fix Import Path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "scripts"))

from scripts.parallel_sprint_runner import run_parallel_execution, default_agent_factory

class TestRunnerLogic(unittest.TestCase):
    
    @patch('scripts.parallel_sprint_runner.analyze_sprint_status')
    @patch('scripts.parallel_sprint_runner.parse_sprint_tasks')
    @patch('scripts.parallel_sprint_runner.SprintConfig')
    @patch('scripts.parallel_sprint_runner.update_sprint_task_status', new_callable=AsyncMock)
    def test_resume_instruction_injection(self, mock_update, mock_config, mock_parse, mock_analyze):
        """
        Verify that RESUME NOTICE is injected into agent factory instructions 
        when a task status is 'in_progress'.
        """
        # Mocks
        mock_analyze.return_value = {
            "total": 1, "done": 0, "in_progress": 1, "blocked": 0, "todo": 0,
            "blocked_tasks": [], "in_progress_tasks": [{'role': 'Backend', 'desc': 'Task 1'}]
        }
        
        # Determine the task to return
        task_in_progress = {
            "role": "Backend",
            "desc": "Task 1",
            "status": "in_progress",
            "blocker_reason": None
        }
        mock_parse.return_value = [task_in_progress]
        
        mock_config.CONCURRENCY_LIMIT = 1
        mock_config.PROMPT_BASE_DIR = "mock_prompts"
        mock_config.get_role_map.return_value = {}
        mock_config.get_sprint_dir.return_value = "mock_dir"

        # Mock Session Service
        mock_session_service = AsyncMock()
        mock_session_service.create_session.return_value = None
        
        # Mock Runner to avoid infinite loop or actual execution
        # We need to mock the `Runner` class in parallel_sprint_runner module
        with patch('scripts.parallel_sprint_runner.Runner') as MockRunnerClass:
            mock_runner_instance = MockRunnerClass.return_value
            # configure run_async to yield nothing effectively (empty async generator)
            async def empty_generator(*args, **kwargs):
                if False: yield # make it a generator
            
            mock_runner_instance.run_async = empty_generator

            # Mock Agent Factory to capture calls
            mock_agent_factory = MagicMock()
            mock_agent = MagicMock()
            mock_agent_factory.return_value = mock_agent

            # Execute
            asyncio.run(run_parallel_execution(
                mock_session_service, 
                "Framework Instruction", 
                "mock_sprint.md", 
                mock_agent_factory
            ))
            
            # Verify
            mock_agent_factory.assert_called()
            args, kwargs = mock_agent_factory.call_args
            instruction_passed = kwargs['instruction']
            
            print(f"DEBUG: Captured Instruction:\n{instruction_passed}")
            
            self.assertIn("=== RESUME NOTICE ===", instruction_passed, 
                          "RESUME NOTICE should be present for in_progress task")
            self.assertIn("Resume where it left off", instruction_passed)

    @patch('scripts.parallel_sprint_runner.analyze_sprint_status')
    @patch('scripts.parallel_sprint_runner.parse_sprint_tasks')
    @patch('scripts.parallel_sprint_runner.SprintConfig')
    @patch('scripts.parallel_sprint_runner.update_sprint_task_status', new_callable=AsyncMock)
    def test_unblock_instruction_injection(self, mock_update, mock_config, mock_parse, mock_analyze):
        """
        Verify that UNBLOCK NOTICE is injected into agent factory instructions 
        when a task status is 'blocked'.
        """
        # Mocks
        mock_analyze.return_value = {
            "total": 1, "done": 0, "in_progress": 0, "blocked": 1, "todo": 0,
            "blocked_tasks": [{'role': 'DevOps', 'desc': 'Task 2'}], "in_progress_tasks": []
        }
        
        task_blocked = {
            "role": "DevOps",
            "desc": "Task 2",
            "status": "blocked",
            "blocker_reason": "Missing Config"
        }
        mock_parse.return_value = [task_blocked]
        
        mock_config.CONCURRENCY_LIMIT = 1
        mock_config.get_role_map.return_value = {}
        mock_config.get_sprint_dir.return_value = "mock_dir"

        mock_session_service = AsyncMock()

        with patch('scripts.parallel_sprint_runner.Runner') as MockRunnerClass:
            mock_runner_instance = MockRunnerClass.return_value
            async def empty_generator(*args, **kwargs):
                if False: yield
            mock_runner_instance.run_async = empty_generator

            mock_agent_factory = MagicMock()
            mock_agent_factory.return_value = MagicMock()

            # Execute
            asyncio.run(run_parallel_execution(
                mock_session_service, 
                "Framework", 
                "mock_sprint.md", 
                mock_agent_factory
            ))
            
            # Verify
            args, kwargs = mock_agent_factory.call_args
            instruction_passed = kwargs['instruction']
            
            print(f"DEBUG: Captured Instruction:\n{instruction_passed}")
            
            self.assertIn("=== UNBLOCK NOTICE ===", instruction_passed,
                          "UNBLOCK NOTICE should be present for blocked task")
            self.assertIn("Missing Config", instruction_passed,
                          "Blocker reason should be included in instruction")

if __name__ == "__main__":
    unittest.main()
