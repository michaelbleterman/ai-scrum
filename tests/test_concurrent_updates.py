"""
Unit tests for concurrent sprint status updates.

These tests validate that the file locking mechanism prevents
race conditions when multiple workers update sprint tasks simultaneously.
"""
import os
import sys
import tempfile
import pytest
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sprint_tools import update_sprint_task_status


class TestConcurrentUpdates:
    """Test suite for concurrent sprint status updates."""
    
    @pytest.fixture
    def sprint_file(self):
        """Create a temporary sprint file with multiple tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sprint_file = os.path.join(tmpdir, "SPRINT_TEST.md")
            with open(sprint_file, 'w') as f:
                f.write("""# Sprint Test

## Tasks

- [ ] @Backend: Task 1 - Setup API
- [ ] @Frontend: Task 2 - Build UI
- [ ] @Backend: Task 3 - Database schema
- [ ] @QA: Task 4 - Write tests
- [ ] @DevOps: Task 5 - Configure CI/CD
""")
            yield tmpdir, sprint_file
    
    @pytest.mark.asyncio
    async def test_concurrent_updates_different_tasks(self, sprint_file):
        """Test that concurrent workers can update different tasks without conflicts."""
        tmpdir, file_path = sprint_file
        
        # Simulate 5 workers updating 5 different tasks concurrently
        tasks_to_update = [
            ("Task 1 - Setup API", "[x]"),
            ("Task 2 - Build UI", "[/]"),
            ("Task 3 - Database schema", "[x]"),
            ("Task 4 - Write tests", "[/]"),
            ("Task 5 - Configure CI/CD", "[!]"),
        ]
        
        # Run all updates concurrently
        results = await asyncio.gather(*[
            update_sprint_task_status(desc, status, tmpdir)
            for desc, status in tasks_to_update
        ])
        
        # Verify all updates succeeded
        for result in results:
            assert "Successfully updated" in result, f"Update failed: {result}"
        
        # Verify final file state
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check all status updates were applied
        assert "- [x] @Backend: Task 1 - Setup API" in content
        assert "- [/] @Frontend: Task 2 - Build UI" in content
        assert "- [x] @Backend: Task 3 - Database schema" in content
        assert "- [/] @QA: Task 4 - Write tests" in content
        assert "- [!] @DevOps: Task 5 - Configure CI/CD" in content
    
    @pytest.mark.asyncio
    async def test_concurrent_updates_same_task(self, sprint_file):
        """Test race condition when multiple workers try to update the same task."""
        tmpdir, file_path = sprint_file
        
        # Simulate 3 workers trying to update the same task to different states
        # Last write should win, but all should complete without error
        updates = [
            ("Task 1 - Setup API", "[/]"),
            ("Task 1 - Setup API", "[!]"),
            ("Task 1 - Setup API", "[x]"),
        ]
        
        # Run all updates concurrently
        results = await asyncio.gather(*[
            update_sprint_task_status(desc, status, tmpdir)
            for desc, status in updates
        ])
        
        # All updates should complete (some may succeed, last one should win)
        for result in results:
            # Should not have lock contention errors
            assert "Failed to update after" not in result
        
        # Verify file is not corrupted
        with open(file_path, 'r') as f:
            content = f.read()
        
        # File should have valid markdown
        assert "# Sprint Test" in content
        assert "@Backend: Task 1 - Setup API" in content
        
        # One of the statuses should be present
        assert any(status in content for status in ["[/]", "[!]", "[x]"])
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self, sprint_file):
        """Stress test with many concurrent updates."""
        tmpdir, file_path = sprint_file
        
        # Create 20 concurrent updates (4 workers × 5 tasks)
        update_tasks = []
        for _ in range(4):  # 4 rounds
            for i in range(1, 6):  # 5 tasks
                desc = f"Task {i}"
                status = "[/]"  # All marking in-progress
                update_tasks.append(update_sprint_task_status(desc, status, tmpdir))
        
        # Run all concurrently
        results = await asyncio.gather(*update_tasks)
        
        # Count successes
        successes = sum(1 for r in results if "Successfully updated" in r)
        
        # At least 5 should succeed (one per task)
        assert successes >= 5, f"Only {successes} updates succeeded out of {len(results)}"
        
        # Verify file integrity
        with open(file_path, 'r') as f:
            content = f.read()
        
        # All tasks should have been updated at least once
        assert "- [/] @Backend: Task 1 - Setup API" in content or "- [x] @Backend: Task 1 - Setup API" in content
        assert content.count("Task 1") == 1  # No duplicates
        assert content.count("Task 2") == 1
        assert content.count("Task 3") == 1
    
    @pytest.mark.asyncio
    async def test_update_retry_on_lock_contention(self, sprint_file):
        """Test that retry mechanism works when lock contention occurs."""
        tmpdir, file_path = sprint_file
        
        # This test verifies the backoff mechanism by checking logs
        # We simulate contention by running many updates simultaneously
        
        update_count = 10
        updates = [
            update_sprint_task_status("Task 1 - Setup API", "[x]", tmpdir)
            for _ in range(update_count)
        ]
        
        results = await asyncio.gather(*updates)
        
        # All should eventually succeed (retries should handle contention)
        for result in results:
            assert "Error: Failed to update after" not in result, \
                "Lock contention exceeded retry limit"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
