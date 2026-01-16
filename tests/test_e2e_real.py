import asyncio
import os
import unittest
import sys
import shutil
import time

# Fix Import Path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "scripts"))

from google.adk.agents import LlmAgent
from scripts.parallel_sprint_runner import SprintRunner
from scripts.sprint_config import SprintConfig
from unittest.mock import patch
import scripts.sprint_tools

class TestE2EReal(unittest.TestCase):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SPRINT_DIR = os.path.join(BASE_DIR, "project_tracking")
    TEST_SPRINT_FILE = os.path.join(SPRINT_DIR, "SPRINT_E2E.md")
    
    def setUp(self):
        pass
        
        # Ensure the sprint directory exists
        if not os.path.exists(self.SPRINT_DIR):
            os.makedirs(self.SPRINT_DIR)
            # Create __init__.py to make it a package
            with open(os.path.join(self.SPRINT_DIR, "__init__.py"), "w") as f:
                f.write("")
        
        # Clean up previous artifacts
        for f in ["QA_REPORT.md", "DEMO_WALKTHROUGH.md", "SPRINT_REPORT.md", "dummy_math.py"]:
            path = os.path.join(self.SPRINT_DIR, f)
            if os.path.exists(path):
                os.remove(path)
        
        # Reset Backlog (optional, or just append)
        backlog_path = os.path.join(self.SPRINT_DIR, "backlog.md")
        if not os.path.exists(backlog_path):
            with open(backlog_path, "w") as f:
                f.write("# Backlog\n")

        # Set CWD to BASE_DIR so agents write to the test environment
        os.chdir(self.BASE_DIR)

        # Create E2E Sprint with INTENTIONAL DEFECT
        with open(self.TEST_SPRINT_FILE, "w", encoding="utf-8") as f:
            f.write("""# Sprint E2E
**Goal:** Verify full lifecycle with defect fix.

### @Backend Tasks
- [ ] Create `project_tracking/dummy_math.py` with function `add(a, b)` that returns `a - b` (INTENTIONAL BUG) [POINTS:3].

### @Frontend Tasks
- [ ] Create `project_tracking/dummy_ui.txt` with text "Hello World" [POINTS:1].
""")


    def test_full_lifecycle(self):
        print("\n\n=== STARTING E2E TEST ===")
        
        # Set project root to BASE_DIR so it uses the .agent/project_tracking folder
        SprintConfig.set_project_root(self.BASE_DIR)
        print(f"[Test] Project root set to: {SprintConfig.PROJECT_ROOT}")
        print(f"[Test] Sprint directory: {SprintConfig.get_sprint_dir()}")
        
        # Custom input callback for Demo phase
        def mock_input(prompt):
            print(f"[Test Input] {prompt} returning 'Great demo!'")
            return "Great demo!"

        # Agent factory compatible with new signature
        def agent_factory(name, instruction, tools, model=None, agent_role=None):
            # Use role-based model selection if available
            if model is None:
                if agent_role:
                    model = SprintConfig.get_model_for_agent(agent_role)
                else:
                    model = SprintConfig.MODEL_NAME
            return LlmAgent(name=name, instruction=instruction, tools=tools, model=model)

        # Mock Context Discovery to ensure agents don't get confused by the root repo
        mock_context = {
            "tech_stack": ["Python"],
            "languages": {"Python": 100},
            "package_managers": ["pip"],
            "key_files": ["requirements.txt"],
            "primary_language": "Python"
        }
        
        # Patch discover_project_context in sprint_tools
        with patch('scripts.sprint_tools.discover_project_context', return_value=str(mock_context)):
            runner = SprintRunner(agent_factory=agent_factory, input_callback=mock_input)
            
            # Run the cycle with exit code handling
            try:
                # Set guard for child processes (agents)
                # Removed recursion guard
                asyncio.run(runner.run_cycle())
            except asyncio.CancelledError:
                print("[Test] Execution cancelled gracefully.")
            except Exception as e:
                self.fail(f"Execution failed with exception: {e}")
        
        # --- CONTEXT DISCOVERY VALIDATION ---
        print("\n[Test] Validating context discovery...")
        
        # Find the most recent timestamped log file in project_tracking/logs
        log_dir = os.path.join(self.SPRINT_DIR, "logs")
        log_path = None
        
        if os.path.exists(log_dir):
            # Get all log files and find the most recent one
            log_files = [f for f in os.listdir(log_dir) if f.startswith("sprint_") and f.endswith(".log")]
            if log_files:
                # Sort by modification time, most recent first
                log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)
                log_path = os.path.join(log_dir, log_files[0])
                print(f"[Test] Found log file: {log_files[0]}")
        
        # Fallback to old centralized log location if project-specific log not found
        if not log_path or not os.path.exists(log_path):
            fallback_path = os.path.join(self.BASE_DIR, "logs", "sprint_debug.log")
            if os.path.exists(fallback_path):
                log_path = fallback_path
                print(f"[Test] Using fallback log: sprint_debug.log")
        
        if log_path and os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                log_content = f.read()
                
                # Verify discover_project_context was called
                if "discover_project_context" in log_content:
                    print("[Test] ✓ Context discovery tool was used")
                else:
                    print("[Test] ⚠️  discover_project_context not found in logs")
                
                # Verify search_codebase was available (may or may not be used in this simple test)
                if "search_codebase" in log_content:
                    print("[Test] ✓ Search codebase tool was used")
        else:
            print("[Test] ⚠️  Log file not found, skipping context validation")
        
        # --- VALIDATION ---
        
        # 1. Check Files Exists
        qa_report_path = os.path.join(self.SPRINT_DIR, "QA_REPORT.md")
        demo_path = os.path.join(self.SPRINT_DIR, "DEMO_WALKTHROUGH.md")
        retro_path = os.path.join(self.SPRINT_DIR, "SPRINT_REPORT.md")
        backlog_path = os.path.join(self.SPRINT_DIR, "backlog.md")
        
        self.assertTrue(os.path.exists(qa_report_path), "QA Report missing")
        self.assertTrue(os.path.exists(demo_path), "Demo Walkthrough missing")
        self.assertTrue(os.path.exists(retro_path), "Sprint Report missing")
        self.assertTrue(os.path.exists(backlog_path), "Backlog missing")
        
        # 2. Check Defect was Created and Resolved
        with open(self.TEST_SPRINT_FILE, "r") as f:
            content = f.read()
            
            # Check if DEFECT was created (Standard Behavior) or proactively fixed (Smart Agent Behavior)
            if "DEFECT" in content:
                self.assertIn("- [x] DEFECT", content, "DEFECT task was not resolved")
            else:
                print("[Test] No DEFECT task found - Assuming proactive fix by agent")
            
            # Assert Task Count / Status
            # We expect at least one original task per role and one defect.
            # And ALL must be [x]
            self.assertFalse("- [ ]" in content, "Found incomplete tasks [ ] in sprint file")
            self.assertFalse("- [/]" in content, "Found in-progress tasks [/] in sprint file")
            
            # Check for Story Points and Turn Usage tracking
            self.assertIn("TURNS_ESTIMATED", content, "Tasks missing TURNS_ESTIMATED metadata - Agent failed to request budget")
            self.assertIn("TURNS_USED", content, "Tasks missing TURNS_USED metadata - Runner failed to record usage")
            self.assertIn("POINTS:3", content, "Points metadata missing or corrupted")
            
        # 3. Check QA Report Content
        with open(qa_report_path, "r", encoding="utf-8") as f:
            qa_content = f.read()
            self.assertIn("PASSED", qa_content, "QA Report does not contain 'PASSED'")
            
        # 4. Check Retro Content
        with open(retro_path, "r", encoding="utf-8") as f:
            retro_content = f.read()
            self.assertIn("Retrospective", retro_content, "Sprint Report missing Retrospective section")

        # 5. Check Backlog Integrity
        with open(backlog_path, "r", encoding="utf-8") as f:
            backlog_content = f.read()
            self.assertTrue(len(backlog_content) > 10, "Backlog seems empty")
            
        # 6. Check Code Fix (dummy_math.py should have been fixed to return a + b)
        math_path = os.path.join(self.SPRINT_DIR, "dummy_math.py")
        if os.path.exists(math_path):
            with open(math_path, "r") as f:
                code = f.read()
                # We hope the agent fixed it to + or at least removed the - 
                # This is probabilistic with LLMs, but strict checking:
                self.assertIn("+", code, "Math bug (subtraction) likely not fixed to addition")
        else:
            self.fail("dummy_math.py missing")
            
        print("\n=== E2E TEST PASSED ===")

if __name__ == "__main__":
    unittest.main()
