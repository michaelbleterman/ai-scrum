"""
Unit tests for sprint state validation.
"""
import os
import sys
import tempfile
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import after path is set
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
try:
    from parallel_sprint_runner import validate_sprint_state
except ImportError:
    # If imports fail, we'll skip these tests
    pytest.skip("Could not import sprint runner modules", allow_module_level=True)


class TestSprintStateValidation:
    """Test suite for sprint state validation."""
    
    def test_empty_sprint_needs_planning(self):
        """Test that empty sprint file returns 'needs_planning'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sprint_file = os.path.join(tmpdir, "SPRINT_TEST.md")
            
            with open(sprint_file, 'w') as f:
                f.write("# Sprint Test\n\nNo tasks defined yet.")
            
            state = validate_sprint_state(sprint_file)
            assert state == 'needs_planning'
    
    def test_sprint_with_pending_tasks_ready(self):
        """Test that sprint with pending tasks returns 'ready'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sprint_file = os.path.join(tmpdir, "SPRINT_TEST.md")
            
            with open(sprint_file, 'w') as f:
                f.write("""# Sprint Test

## Tasks
- [ ] @Backend: Task 1
- [ ] @Frontend: Task 2
""")
            
            state = validate_sprint_state(sprint_file)
            assert state == 'ready'
    
    def test_sprint_with_in_progress_tasks_ready(self):
        """Test that sprint with in-progress tasks returns 'ready'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sprint_file = os.path.join(tmpdir, "SPRINT_TEST.md")
            
            with open(sprint_file, 'w') as f:
                f.write("""# Sprint Test

## Tasks
- [/] @Backend: Task 1 in progress
- [ ] @Frontend: Task 2
""")
            
            state = validate_sprint_state(sprint_file)
            assert state == 'ready'
    
    def test_sprint_all_completed_returns_completed(self):
        """Test that sprint with all completed tasks returns 'completed'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sprint_file = os.path.join(tmpdir, "SPRINT_TEST.md")
            
            with open(sprint_file, 'w') as f:
                f.write("""# Sprint Test

## Tasks
- [x] @Backend: Task 1 completed
- [x] @Frontend: Task 2 completed
- [x] @QA: Task 3 completed
""")
            
            state = validate_sprint_state(sprint_file)
            assert state == 'completed'
    
    def test_sprint_with_blocked_tasks_ready(self):
        """Test that sprint with blocked tasks returns 'ready' (not completed)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sprint_file = os.path.join(tmpdir, "SPRINT_TEST.md")
            
            with open(sprint_file, 'w') as f:
                f.write("""# Sprint Test

## Tasks
- [x] @Backend: Task 1 completed
- [!] @Frontend: Task 2 blocked
""")
            
            state = validate_sprint_state(sprint_file)
            assert state == 'ready'
    
    def test_sprint_mixed_state_ready(self):
        """Test that sprint with mixed done/pending tasks returns 'ready'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sprint_file = os.path.join(tmpdir, "SPRINT_TEST.md")
            
            with open(sprint_file, 'w') as f:
                f.write("""# Sprint Test

## Tasks
- [x] @Backend: Task 1 completed
- [ ] @Frontend: Task 2 pending
- [/] @QA: Task 3 in progress
""")
            
            state = validate_sprint_state(sprint_file)
            assert state == 'ready'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
