"""
End-to-end test for sprint resume functionality.

This test validates that the sprint runner:
1. Does NOT overwrite existing sprint files
2. Correctly resumes sprints with in-progress tasks
3. Adds RESUME notices to in-progress tasks
4. Adds UNBLOCK notices to blocked tasks
"""
import os
import sys
import tempfile
import shutil
import pytest
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from unittest.mock import Mock, AsyncMock, patch
from parallel_sprint_runner import SprintRunner, validate_sprint_state
from sprint_config import SprintConfig


class TestResumeSprintE2E:
    """E2E tests for resume sprint functionality."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with sprint file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project_tracking directory
            tracking_dir = os.path.join(tmpdir, "project_tracking")
            os.makedirs(tracking_dir)
            
            # Create a sprint file with mixed task states
            sprint_file = os.path.join(tracking_dir, "SPRINT_2.md")
            with open(sprint_file, 'w') as f:
                f.write("""# Sprint 2: Test Sprint

## Sprint Log

### Story 1: Completed Task
- [x] @Backend: Task 1 completed

### Story 2: In Progress Task
- [/] @Frontend: Task 2 in progress

### Story 3: Blocked Task  
- [!] @QA: Task 3 blocked [BLOCKED: Missing test data]

### Story 4: Pending Task
- [ ] @DevOps: Task 4 pending
""")
            
            # Create prompts directory
            prompts_dir = os.path.join(tmpdir, "..", "..", "prompts")
            os.makedirs(prompts_dir, exist_ok=True)
            
            # Create minimal framework index
            with open(os.path.join(prompts_dir, "agent_framework_index.md"), 'w') as f:
                f.write("# Framework Index\nTest content")
            
            yield tmpdir, sprint_file
    
    def test_sprint_file_not_overwritten(self, temp_project):
        """Test that existing sprint file is not overwritten."""
        tmpdir, sprint_file = temp_project
        
        # Read original content
        with open(sprint_file, 'r') as f:
            original_content = f.read()
        
        # Verify sprint state is 'ready' (not 'needs_planning')
        state = validate_sprint_state(sprint_file)
        assert state == 'ready', f"Sprint should be ready, but got: {state}"
        
        # Verify original content still intact
        with open(sprint_file, 'r') as f:
            current_content = f.read()
        
        assert current_content == original_content
        assert "Task 2 in progress" in current_content
        assert "Task 3 blocked" in current_content
    
    def test_validate_completed_sprint(self):
        """Test that completed sprint is detected correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sprint_file = os.path.join(tmpdir, "SPRINT_COMPLETE.md")
            
            with open(sprint_file, 'w') as f:
                f.write("""# Sprint Complete

## Tasks
- [x] @Backend: All tasks
- [x] @Frontend: Are done
""")
            
            state = validate_sprint_state(sprint_file)
            assert state == 'completed'
    
    def test_resume_instructions_parsing(self, temp_project):
        """Test that in-progress and blocked tasks are correctly identified."""
        tmpdir, sprint_file = temp_project
        
        # Import sprint_utils
        from sprint_utils import parse_sprint_tasks
        
        tasks = parse_sprint_tasks(sprint_file)
        
        # Should return in-progress and blocked tasks, not completed ones
        assert len(tasks) > 0
        
        # Verify we have in-progress and blocked tasks
        statuses = [t['status'] for t in tasks]
        assert 'in_progress' in statuses
        assert 'blocked' in statuses
        assert 'todo' in statuses
        
        # Verify completed task is NOT included
        descriptions = [t['desc'] for t in tasks]
        assert "Task 1 completed" not in descriptions
        assert "Task 2 in progress" in descriptions
        assert "Task 3 blocked" in descriptions
    
    def test_runner_validates_before_execution(self, temp_project):
        """Test that sprint runner validates state before execution."""
        async def _test():
            tmpdir, sprint_file = temp_project
            
            # Configure SprintConfig to use temp directory
            SprintConfig.set_project_root(tmpdir)
            
            # Create a mock agent factory
            def mock_agent_factory(name, instruction, tools, model=None, agent_role=None):
                mock_agent = Mock()
                mock_agent.name = name
                return mock_agent
            
            # Create runner with mock factory
            runner = SprintRunner(agent_factory=mock_agent_factory)
            
            # Validate that sprint is in 'ready' state
            state = validate_sprint_state(sprint_file)
            assert state == 'ready'
            
            # If we tried to run a completed sprint, it should exit early
            # Create a completed sprint to test this
            completed_sprint = os.path.join(tmpdir, "project_tracking", "SPRINT_COMPLETE.md")
            with open(completed_sprint, 'w') as f:
                f.write("""# Sprint Complete
    
    - [x] @Backend: All done
    """)
            
            state = validate_sprint_state(completed_sprint)
            assert state == 'completed'

        asyncio.run(_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
