import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path

# Add parent directory to path to import sprint_memory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sprint_memory import SprintMemoryBank

class TestSprintMemory(unittest.TestCase):
    
    def setUp(self):
        """Create temporary directory for testing"""
        self.test_dir = tempfile.mkdtemp()
        self.memory = SprintMemoryBank(
            project_root=self.test_dir,
            enable_memory=True
        )
        
        # Check if setup failed due to missing deps
        if not self.memory.enable_memory:
            print("Skipping tests because memory depends are missing")
            self.skipTest("Memory dependencies (chromadb/sentence-transformers) not installed")
    
    def tearDown(self):
        """Clean up temporary directory"""
        # Close client to allow file cleanup (if method exists)
        if hasattr(self.memory, 'client'):
            # self.memory.client = None # Chroma client doesn't have explicit close
            pass
            
        try:
            shutil.rmtree(self.test_dir)
        except PermissionError:
            print(f"Warning: Could not cleanup {self.test_dir} - file in use?")
    
    def test_store_and_recall(self):
        """Test basic store and recall functionality"""
        # Store a memory
        memory_id = self.memory.store(
            content="Test memory content about API testing",
            memory_type="pattern",
            metadata={"test": True}
        )
        
        self.assertIsNotNone(memory_id)
        self.assertIn("pattern", memory_id)
        
        # Recall the memory
        results = self.memory.recall("API testing", top_k=1)
        
        self.assertEqual(len(results), 1)
        self.assertIn("API testing", results[0]['content'])
        self.assertTrue(results[0]['metadata']['test'] == True or results[0]['metadata']['test'] == "True")
    
    def test_memory_filtering(self):
        """Test filtering by memory type"""
        # Store different types
        self.memory.store("Error resolution", memory_type="error_resolution")
        self.memory.store("Design pattern", memory_type="pattern")
        self.memory.store("Architecture decision", memory_type="decision")
        
        # Filter by type
        errors = self.memory.recall("resolution", memory_type="error_resolution")
        patterns = self.memory.recall("pattern", memory_type="pattern")
        
        self.assertTrue(all(m['metadata']['memory_type'] == 'error_resolution' for m in errors))
        self.assertTrue(all(m['metadata']['memory_type'] == 'pattern' for m in patterns))
    
    def test_semantic_search(self):
        """Test semantic similarity matching"""
        # Store memories
        self.memory.store("Port 5173 occupied by zombie process", memory_type="error_resolution")
        self.memory.store("Database connection timeout after 30s", memory_type="error_resolution")
        
        # Search with semantically similar query
        results = self.memory.recall("process blocking port", top_k=2)
        
        # First result should be about port/process
        self.assertIn("Port", results[0]['content'])
        
        # Note: distance is 0 for identical, < 1 for similar. 
        # ChromaDB default metric is L2 squared distance? Or Cosine?
        # By default Chroma uses l2. Lower is better.
        # But SentenceTransformers usually normalized so cosine distance.
        # Let's just check relative relevant result is first.
        self.assertIn("Port", results[0]['content'])
    
    def test_statistics(self):
        """Test memory bank statistics"""
        # Store various memories
        for i in range(3):
            self.memory.store(f"Pattern {i}", memory_type="pattern")
        for i in range(2):
            self.memory.store(f"Error {i}", memory_type="error_resolution")
        
        stats = self.memory.get_statistics()
        
        self.assertTrue(stats['enabled'])
        self.assertEqual(stats['total_memories'], 5)
        self.assertEqual(stats['by_type']['pattern'], 3)
        self.assertEqual(stats['by_type']['error_resolution'], 2)
    
    def test_disabled_memory(self):
        """Test that memory can be disabled"""
        disabled_memory = SprintMemoryBank(
            project_root=self.test_dir,
            enable_memory=False
        )
        
        result = disabled_memory.store("Test", memory_type="pattern")
        self.assertEqual(result, "")
        
        results = disabled_memory.recall("Test")
        self.assertEqual(results, [])
        
        stats = disabled_memory.get_statistics()
        self.assertFalse(stats['enabled'])


if __name__ == '__main__':
    unittest.main()
