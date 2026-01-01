import asyncio
import os
import unittest
import sys
import shutil
import time

# Fix Import Path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from google.adk.agents import LlmAgent
from scripts.parallel_sprint_runner import SprintRunner
from scripts.sprint_config import SprintConfig

class TestE2EReal(unittest.TestCase):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SPRINT_DIR = os.path.join(BASE_DIR, "project_tracking")
    TEST_SPRINT_FILE = os.path.join(SPRINT_DIR, "SPRINT_E2E.md")
    
    def setUp(self):
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

        # Create E2E Sprint with INTENTIONAL DEFECT
        with open(self.TEST_SPRINT_FILE, "w", encoding="utf-8") as f:
            f.write("""# Sprint E2E
**Goal:** Verify full lifecycle with defect fix.

### @Backend Tasks
- [ ] Create `project_tracking/dummy_math.py` with function `add(a, b)` that returns `a - b` (INTENTIONAL BUG).

### @Frontend Tasks
- [ ] Create `project_tracking/dummy_ui.txt` with text "Hello World".
""")

    def test_full_lifecycle(self):
        print("\n\n=== STARTING E2E TEST ===")
        
        # Custom input callback for Demo phase
        def mock_input(prompt):
            print(f"[Test Input] {prompt} returning 'Great demo!'")
            return "Great demo!"

        # Agent factory (optional, can simulate stronger models if needed)
        def agent_factory(name, instruction, tools, model=None):
            if model is None:
                model = SprintConfig.MODEL_NAME
            # Pass through real agents
            return LlmAgent(name=name, instruction=instruction, tools=tools, model=model)

        runner = SprintRunner(agent_factory=agent_factory, input_callback=mock_input)
        
        # Run the cycle
        asyncio.run(runner.run_cycle())
        
        # --- VALIDATION ---
        
        # 1. Check Files Exists
        self.assertTrue(os.path.exists(os.path.join(self.SPRINT_DIR, "QA_REPORT.md")), "QA Report missing")
        self.assertTrue(os.path.exists(os.path.join(self.SPRINT_DIR, "DEMO_WALKTHROUGH.md")), "Demo Walkthrough missing")
        self.assertTrue(os.path.exists(os.path.join(self.SPRINT_DIR, "SPRINT_REPORT.md")), "Sprint Report missing")
        
        # 2. Check Defect was Created and Resolved
        with open(self.TEST_SPRINT_FILE, "r") as f:
            content = f.read()
            self.assertIn("DEFECT", content, "No DEFECT task created by QA")
            self.assertIn("- [x] DEFECT", content, "DEFECT task was not resolved")
            
        # 3. Check Code Fix (dummy_math.py should have been fixed to return a + b)
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
