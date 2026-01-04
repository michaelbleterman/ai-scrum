"""
Unit tests for write_file overwrite protection.
"""
import os
import sys
import tempfile
import time
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sprint_tools import write_file


class TestWriteFileProtection:
    """Test suite for write_file overwrite protection."""
    
    def test_write_new_file(self):
        """Test writing to a new file succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            result = write_file(test_file, "Hello World")
            
            assert "Successfully wrote" in result
            assert os.path.exists(test_file)
            
            with open(test_file, 'r') as f:
                assert f.read() == "Hello World"
    
    def test_overwrite_protection_default(self):
        """Test that overwriting existing file fails by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            
            # Create initial file
            write_file(test_file, "Original content")
            
            # Attempt to overwrite without explicit permission
            result = write_file(test_file, "New content")
            
            assert "Error" in result
            assert "already exists" in result
            
            # Verify original content unchanged
            with open(test_file, 'r') as f:
                assert f.read() == "Original content"
    
    def test_overwrite_with_permission(self):
        """Test that overwriting with overwrite=True succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            
            # Create initial file
            write_file(test_file, "Original content")
            
            # Overwrite with explicit permission
            result = write_file(test_file, "New content", overwrite=True)
            
            assert "Successfully wrote" in result
            
            # Verify new content
            with open(test_file, 'r') as f:
                assert f.read() == "New content"
    
    def test_backup_created_on_overwrite(self):
        """Test that NO backup is created when overwriting (feature disabled)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            
            # Create initial file
            write_file(test_file, "Original content")
            
            # Wait a moment
            time.sleep(0.1)
            
            # Overwrite with permission
            write_file(test_file, "New content", overwrite=True)
            
            # Check for backup file - SHOULD BE NONE as feature is disabled
            backup_files = [f for f in os.listdir(tmpdir) if f.startswith("test.txt.backup")]
            assert len(backup_files) == 0, "Backup files should not be created"
            
            # Verify content is new
            with open(test_file, 'r') as f:
                assert f.read() == "New content"
    
    def test_sprint_file_protection(self):
        """Test that attempting to overwrite a SPRINT_*.md file fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sprint_file = os.path.join(tmpdir, "SPRINT_2.md")
            
            # Create sprint file
            write_file(sprint_file, "# Sprint 2\n\n- [ ] Task 1")
            
            # Attempt to overwrite
            result = write_file(sprint_file, "# Completely new sprint")
            
            assert "Error" in result
            assert "already exists" in result
            
            # Verify original content preserved
            with open(sprint_file, 'r') as f:
                content = f.read()
                assert "Task 1" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
