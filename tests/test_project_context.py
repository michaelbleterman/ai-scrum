import os
import sys
import unittest
import tempfile
import shutil
import json

# Fix Import Path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "scripts"))

from scripts.sprint_tools import discover_project_context


class TestProjectContext(unittest.TestCase):
    """Test suite for project context discovery functionality"""
    
    def setUp(self):
        """Create temporary test directories for each test"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary test directories"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_discover_nodejs_project(self):
        """Test that discover_project_context correctly identifies Node.js projects"""
        # Create package.json
        package_json = {
            "name": "test-app",
            "dependencies": {
                "express": "^4.18.0",
                "react": "^18.0.0"
            }
        }
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            json.dump(package_json, f)
        
        # Create some JS files
        os.makedirs(os.path.join(self.test_dir, "src"), exist_ok=True)
        with open(os.path.join(self.test_dir, "src", "app.js"), "w") as f:
            f.write("console.log('test');")
        
        # Discover context
        result = discover_project_context(self.test_dir)
        context = json.loads(result)
        
        # Assertions
        self.assertIn("Node.js", context["tech_stack"])
        self.assertIn("Express.js", context["frameworks"])
        self.assertIn("React", context["frameworks"])
        self.assertIn("npm/yarn", context["package_managers"])
        self.assertIn("package.json", context["key_files"])
        self.assertIn("JavaScript/TypeScript", context["languages"])
    
    def test_discover_python_project(self):
        """Test that discover_project_context correctly identifies Python projects"""
        # Create requirements.txt
        with open(os.path.join(self.test_dir, "requirements.txt"), "w") as f:
            f.write("flask==2.0.0\nrequests==2.28.0\n")
        
        # Create some Python files
        os.makedirs(os.path.join(self.test_dir, "src"), exist_ok=True)
        with open(os.path.join(self.test_dir, "src", "app.py"), "w") as f:
            f.write("print('test')")
        
        # Discover context
        result = discover_project_context(self.test_dir)
        context = json.loads(result)
        
        # Assertions
        self.assertIn("Python", context["tech_stack"])
        self.assertIn("pip", context["package_managers"])
        self.assertIn("requirements.txt", context["key_files"])
        self.assertIn("Python", context["languages"])
    
    def test_discover_mixed_project(self):
        """Test context discovery in a project with both frontend and backend"""
        # Create package.json (Node.js frontend)
        package_json = {"name": "test-app", "dependencies": {"react": "^18.0.0"}}
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            json.dump(package_json, f)
        
        # Create requirements.txt (Python backend)
        with open(os.path.join(self.test_dir, "requirements.txt"), "w") as f:
            f.write("flask==2.0.0\n")
        
        # Create files
        os.makedirs(os.path.join(self.test_dir, "frontend"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "backend"), exist_ok=True)
        
        with open(os.path.join(self.test_dir, "frontend", "App.jsx"), "w") as f:
            f.write("export default function App() {}")
        
        with open(os.path.join(self.test_dir, "backend", "server.py"), "w") as f:
            f.write("from flask import Flask")
        
        # Discover context
        result = discover_project_context(self.test_dir)
        context = json.loads(result)
        
        # Assertions - should detect both stacks
        self.assertIn("Node.js", context["tech_stack"])
        self.assertIn("Python", context["tech_stack"])
        self.assertIn("React", context["frameworks"])
        self.assertIn("JavaScript/TypeScript", context["languages"])
        self.assertIn("Python", context["languages"])
    
    def test_discover_empty_project(self):
        """Test context discovery in an empty directory"""
        result = discover_project_context(self.test_dir)
        context = json.loads(result)
        
        # Should return empty lists but not error
        self.assertEqual(context["tech_stack"], [])
        self.assertEqual(context["frameworks"], [])
        self.assertEqual(context["package_managers"], [])
    
    def test_primary_language_detection(self):
        """Test that primary language is correctly identified"""
        # Create more JS files than Python files
        os.makedirs(os.path.join(self.test_dir, "src"), exist_ok=True)
        
        for i in range(5):
            with open(os.path.join(self.test_dir, "src", f"file{i}.js"), "w") as f:
                f.write("console.log('test');")
        
        with open(os.path.join(self.test_dir, "src", "script.py"), "w") as f:
            f.write("print('test')")
        
        result = discover_project_context(self.test_dir)
        context = json.loads(result)
        
        # Primary language should be JavaScript/TypeScript
        self.assertEqual(context.get("primary_language"), "JavaScript/TypeScript")
        self.assertGreater(context["languages"]["JavaScript/TypeScript"], 
                          context["languages"]["Python"])


if __name__ == "__main__":
    unittest.main()
