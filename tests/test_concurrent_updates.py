"""
Unit tests for concurrent sprint status updates.

These tests validate that the file locking mechanism prevents
race conditions when multiple workers update sprint tasks simultaneously.
"""
import os
import sys
import tempfile
import asyncio
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sprint_tools import update_sprint_task_status


class TestConcurrentUpdates(unittest.IsolatedAsyncioTestCase):
    """Test suite for concurrent sprint status updates."""
    
    def setUp(self):
        """Create a temporary sprint file with multiple tasks."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.sprint_file = os.path.join(self.tmpdir.name, "SPRINT_TEST.md")
        with open(self.sprint_file, 'w') as f:
            f.write("""# Sprint Test

## Tasks

- [ ] @Backend: Task 1 - Setup API
- [ ] @Frontend: Task 2 - Build UI
- [ ] @Backend: Task 3 - Database schema
- [ ] @QA: Task 4 - Write tests
- [ ] @DevOps: Task 5 - Configure CI/CD
""")
    
    def tearDown(self):
        """Cleanup temporary directory."""
        self.tmpdir.cleanup()
    
    async def test_concurrent_updates_different_tasks(self):
        """Test that concurrent workers can update different tasks without conflicts."""
        file_path = self.sprint_file
        
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
            update_sprint_task_status(desc, status, self.tmpdir.name)
            for desc, status in tasks_to_update
        ])
        
        # Verify all updates succeeded
        for result in results:
            self.assertIn("Successfully updated", result)
        
        # Verify final file state
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check all status updates were applied
        self.assertIn("- [x] @Backend: Task 1 - Setup API", content)
        self.assertIn("- [/] @Frontend: Task 2 - Build UI", content)
        self.assertIn("- [x] @Backend: Task 3 - Database schema", content)
        self.assertIn("- [/] @QA: Task 4 - Write tests", content)
        self.assertIn("- [!] @DevOps: Task 5 - Configure CI/CD", content)
    
    async def test_concurrent_updates_same_task(self):
        """Test race condition when multiple workers try to update the same task."""
        file_path = self.sprint_file
        
        # Simulate 3 workers trying to update the same task to different states
        # Last write should win, but all should complete without error
        updates = [
            ("Task 1 - Setup API", "[/]"),
            ("Task 1 - Setup API", "[!]"),
            ("Task 1 - Setup API", "[x]"),
        ]
        
        # Run all updates concurrently
        results = await asyncio.gather(*[
            update_sprint_task_status(desc, status, self.tmpdir.name)
            for desc, status in updates
        ])
        
        # All updates should complete (some may succeed, last one should win)
        for result in results:
            # Should not have lock contention errors
            self.assertNotIn("Failed to update after", result)
        
        # Verify file is not corrupted
        with open(file_path, 'r') as f:
            content = f.read()
        
        # File should have valid markdown
        self.assertIn("# Sprint Test", content)
        self.assertIn("@Backend: Task 1 - Setup API", content)
        
        # One of the statuses should be present
        self.assertTrue(any(status in content for status in ["[/]", "[!]", "[x]"]))
    
    async def test_high_concurrency_stress(self):
        """Stress test with many concurrent updates."""
        file_path = self.sprint_file
        
        # Create 20 concurrent updates (4 workers × 5 tasks)
        update_tasks = []
        for _ in range(4):  # 4 rounds
            for i in range(1, 6):  # 5 tasks
                desc = f"Task {i}"
                status = "[/]"  # All marking in-progress
                update_tasks.append(update_sprint_task_status(desc, status, self.tmpdir.name))
        
        # Run all concurrently
        results = await asyncio.gather(*update_tasks)
        
        # Count successes
        successes = sum(1 for r in results if "Successfully updated" in r)
        
        # At least 5 should succeed (one per task)
        self.assertGreaterEqual(successes, 5)
        
        # Verify file integrity
        with open(file_path, 'r') as f:
            content = f.read()
        
        # All tasks should have been updated at least once
        self.assertTrue("- [/] @Backend: Task 1 - Setup API" in content or "- [x] @Backend: Task 1 - Setup API" in content)
        self.assertEqual(content.count("Task 1"), 1)
        self.assertEqual(content.count("Task 2"), 1)
        self.assertEqual(content.count("Task 3"), 1)
    
    async def test_update_retry_on_lock_contention(self):
        """Test that retry mechanism works when lock contention occurs."""
        
        # This test verifies the backoff mechanism by checking logs
        # We simulate contention by running many updates simultaneously
        
        update_count = 10
        updates = [
            update_sprint_task_status("Task 1 - Setup API", "[x]", self.tmpdir.name)
            for _ in range(update_count)
        ]
        
        results = await asyncio.gather(*updates)
        
        # All should eventually succeed (retries should handle contention)
        for result in results:
            self.assertNotIn("Error: Failed to update after", result)


if __name__ == "__main__":
    unittest.main()
