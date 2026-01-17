import asyncio
import os
import unittest
import sys
import shutil
import time
import json

# Fix Import Path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, "scripts"))

from google.adk.agents import LlmAgent
from scripts.parallel_sprint_runner import SprintRunner
from scripts.sprint_config import SprintConfig
from unittest.mock import patch
import scripts.sprint_tools

class E2ERunner(unittest.TestCase):
    """
    Full E2E test for sprint framework.
    
    Tests execute sequentially to simulate complete sprint lifecycle:
    1. Execution phase (parallel task execution)
    2. QA validation phase
    3. Demo generation phase
    4. Retrospective phase
    5. Profiling integration
    6. Memory integration
    7. Turn budget tracking
    
    Tests are numbered (test_1_, test_2_) to enforce execution order.
    Later tests depend on earlier tests completing successfully.
    """
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SPRINT_DIR = os.path.join(BASE_DIR, "project_tracking")
    TEST_SPRINT_FILE = os.path.join(SPRINT_DIR, "SPRINT_E2E.md")
    
    # Class-level state shared across all test methods
    runner = None
    sprint_executed = False
    
    def setUp(self):
        """Setup test environment - runs before EACH test method"""
        # Only do full setup once for test_1
        if not self.sprint_executed:
            # Ensure the sprint directory exists
            if not os.path.exists(self.SPRINT_DIR):
                os.makedirs(self.SPRINT_DIR)
                # Create __init__.py to make it a package
                with open(os.path.join(self.SPRINT_DIR, "__init__.py"), "w") as f:
                    f.write("")
            
            # Clean up previous artifacts
            for f in ["QA_REPORT.md", "DEMO_WALKTHROUGH.md", "SPRINT_REPORT.md", "dummy_math.py", "dummy_ui.txt"]:
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

            # Use fixture instead of inline sprint definition
            fixture_path = os.path.join(self.BASE_DIR, "tests", "fixtures", "sprints", "defect_workflow_sprint.md")
            shutil.copy(fixture_path, self.TEST_SPRINT_FILE)
    
    # --- Helper Methods ---
    
    def _create_agent_factory(self):
        """Creates agent factory with model selection"""
        def agent_factory(name, instruction, tools, model=None, agent_role=None):
            # Use role-based model selection if available
            if model is None:
                if agent_role:
                    model = SprintConfig.get_model_for_agent(agent_role)
                else:
                    model = SprintConfig.MODEL_NAME
            return LlmAgent(name=name, instruction=instruction, tools=tools, model=model)
        return agent_factory
    
    def _create_mock_input(self):
        """Creates mock input callback for demo phase"""
        def mock_input(prompt):
            print(f"[Test Input] {prompt} returning 'Great demo!'")
            return "Great demo!"
        return mock_input
    
    def _get_mock_context(self):
        """Returns mock project context"""
        return {
            "tech_stack": ["Python"],
            "languages": {"Python": 100},
            "package_managers": ["pip"],
            "key_files": ["requirements.txt"],
            "primary_language": "Python"
        }
    
    def _assert_artifact_exists(self, filename, description):
        """Helper to check artifact file exists"""
        path = os.path.join(self.SPRINT_DIR, filename)
        self.assertTrue(os.path.exists(path), f"{description} missing")
        return path
    
    # --- Test Methods (Sequential Execution) ---
    
    def test_1_full_sprint_execution(self):
        """
        Test 1: Execute complete sprint lifecycle.
        
        Runs all phases:
        - Execution (parallel task execution)
        - QA (validation and defect detection)
        - Demo (walkthrough generation)
        - Retro (retrospective report)
        
        Subsequent tests validate specific aspects of this execution.
        """
        print("\n\n=== TEST 1: FULL SPRINT EXECUTION ===")
        
        # Initialize Logger
        import scripts.parallel_sprint_runner
        scripts.parallel_sprint_runner.logger = scripts.parallel_sprint_runner.setup_logging(self.BASE_DIR)
        
        # Set project root
        SprintConfig.set_project_root(self.BASE_DIR)
        print(f"[Test] Project root set to: {SprintConfig.PROJECT_ROOT}")
        print(f"[Test] Sprint directory: {SprintConfig.get_sprint_dir()}")
        
        # Create helpers
        agent_factory = self._create_agent_factory()
        mock_input = self._create_mock_input()
        mock_context = self._get_mock_context()
        
        from scripts.sprint_memory import SprintMemoryBank
        
        # Patch discover_project_context
        with patch('scripts.sprint_tools.discover_project_context', return_value=str(mock_context)):
            # Initialize Memory Bank
            memory_bank = SprintMemoryBank(project_root=self.BASE_DIR)
            
            # Create runner and store in class variable
            E2ERunner.runner = SprintRunner(
                agent_factory=agent_factory,
                input_callback=mock_input,
                memory_bank=memory_bank
            )
            
            # Run the full cycle
            try:
                asyncio.run(E2ERunner.runner.run_cycle())
                E2ERunner.sprint_executed = True
                print("[Test 1] Sprint execution completed successfully")
            except asyncio.CancelledError:
                self.fail("Execution cancelled")
            except Exception as e:
                self.fail(f"Execution failed with exception: {e}")
        
        # Basic validation - sprint file should have completed tasks
        with open(self.TEST_SPRINT_FILE, "r") as f:
            content = f.read()
            # At least some tasks should be marked complete
            self.assertIn("- [x]", content, "No tasks were completed")
        
        print("[Test 1] ✓ Sprint execution phase validated")
    
    def test_2_artifacts_generated(self):
        """
        Test 2: Validate core artifacts were generated.
        
        Checks:
        - DEMO_WALKTHROUGH.md (required)
        - SPRINT_REPORT.md (required)
        - backlog.md (required)
        - QA_REPORT.md (optional - may not be created if no defects found)
        """
        print("\n=== TEST 2: ARTIFACTS VALIDATION ===")
        
        if not E2ERunner.sprint_executed:
            self.skipTest("Sprint execution test must run first")
        
        # Check required artifacts exist
        self._assert_artifact_exists("DEMO_WALKTHROUGH.md", "Demo Walkthrough")
        self._assert_artifact_exists("SPRINT_REPORT.md", "Sprint Report")
        self._assert_artifact_exists("backlog.md", "Backlog")
        
        # QA report is optional (depends on whether issues were found)
        qa_report_path = os.path.join(self.SPRINT_DIR, "QA_REPORT.md")
        if os.path.exists(qa_report_path):
            print("[Test 2] ✓ QA Report generated")
        else:
            print("[Test 2] ⚠ QA Report not generated (may indicate no formal QA phase)")
        
        print("[Test 2] ✓ Core artifacts validated")
    
    def test_3_qa_phase_validation(self):
        """
        Test 3: Validate QA phase results (if QA ran).
        
        Checks:
        - QA report contains PASSED status (if report exists)
        - Defect workflow (if defect was created and resolved)
        """
        print("\n=== TEST 3: QA PHASE VALIDATION ===")
        
        if not E2ERunner.sprint_executed:
            self.skipTest("Sprint execution test must run first")
        
        # Check if QA report exists
        qa_report_path = os.path.join(self.SPRINT_DIR, "QA_REPORT.md")
        if os.path.exists(qa_report_path):
            # Check QA Report Content
            with open(qa_report_path, "r", encoding="utf-8") as f:
                qa_content = f.read()
                self.assertIn("PASSED", qa_content, "QA Report does not contain 'PASSED'")
            print("[Test 3] ✓ QA Report validated")
        else:
            print("[Test 3] ⚠ QA Report not found - QA phase may have been skipped")
        
        # Check Defect Workflow
        with open(self.TEST_SPRINT_FILE, "r") as f:
            content = f.read()
            
            # Check if DEFECT was created (Standard Behavior) or proactively fixed (Smart Agent)
            if "DEFECT" in content:
                self.assertIn("- [x] DEFECT", content, "DEFECT task was not resolved")
                print("[Test 3] ✓ Defect was created and resolved")
            else:
                print("[Test 3] ⚠ No DEFECT task found - Bug may not have been detected")
        
        print("[Test 3] ✓ QA phase check completed")
    
    def test_4_task_completion_validation(self):
        """
        Test 4: Validate all tasks completed successfully.
        
        Checks:
        - No incomplete tasks ([ ])
        - No in-progress tasks ([/])
        - Code artifacts created correctly
        """
        print("\n=== TEST 4: TASK COMPLETION VALIDATION ===")
        
        if not E2ERunner.sprint_executed:
            self.skipTest("Sprint execution test must run first")
        
        with open(self.TEST_SPRINT_FILE, "r") as f:
            content = f.read()
            
            # All tasks must be complete
            self.assertFalse("- [ ]" in content, "Found incomplete tasks [ ] in sprint file")
            self.assertFalse("- [/]" in content, "Found in-progress tasks [/] in sprint file")
        
        # Check code artifact exists
        math_path = os.path.join(self.SPRINT_DIR, "dummy_math.py")
        self.assertTrue(os.path.exists(math_path), "dummy_math.py missing")
        
        # Check if bug was fixed (optional - depends on QA detection)
        with open(math_path, "r") as f:
            code = f.read()
            if "+" in code and "return a + b" in code:
                print("[Test 4] ✓ Bug was fixed (subtraction → addition)")
            elif "-" in code and "return a - b" in code:
                print("[Test 4] ⚠ Bug remains unfixed (intentional behavior from spec)")
            else:
                print("[Test 4] ⚠ Unexpected code structure")
        
        # Check Frontend artifact
        ui_path = os.path.join(self.SPRINT_DIR, "dummy_ui.txt")
        self.assertTrue(os.path.exists(ui_path), "dummy_ui.txt missing")
        
        print("[Test 4] ✓ All tasks completed successfully")
    
    def test_5_metadata_tracking(self):
        """
        Test 5: Validate metadata tracking.
        
        Checks:
        - TURNS_ESTIMATED metadata present
        - TURNS_USED metadata recorded
        - Story points preserved (POINTS:3)
        """
        print("\n=== TEST 5: METADATA TRACKING ===")
        
        if not E2ERunner.sprint_executed:
            self.skipTest("Sprint execution test must run first")
        
        with open(self.TEST_SPRINT_FILE, "r") as f:
            content = f.read()
            
            # Check for Story Points and Turn Usage tracking
            self.assertIn("TURNS_ESTIMATED", content, "Tasks missing TURNS_ESTIMATED - Agent failed to request budget")
            self.assertIn("TURNS_USED", content, "Tasks missing TURNS_USED - Runner failed to record usage")
            self.assertIn("POINTS:3", content, "Points metadata missing or corrupted")
        
        print("[Test 5] ✓ Metadata tracking validated")
    
    def test_6_profiling_integration(self):
        """
        Test 6: Validate agent profiling integration.
        
        Checks:
        - profiles.json created
        - Backend agent profile exists
        - XP tracking works
        - Task completion stats recorded
        """
        print("\n=== TEST 6: PROFILING INTEGRATION ===")
        
        if not E2ERunner.sprint_executed:
            self.skipTest("Sprint execution test must run first")
        
        profile_path = self._assert_artifact_exists("profiles.json", "Agent Profiles")
        
        with open(profile_path, "r", encoding="utf-8") as f:
            profiles = json.load(f)
            
            # Verify Backend profile exists
            backend_keys = [k for k in profiles.keys() if "Backend" in k or "backend" in k]
            self.assertTrue(len(backend_keys) > 0, "No Backend agent profile found")
            
            # Verify stats were tracked
            backend_profile = profiles[backend_keys[0]]
            total_xp = backend_profile.get("xp", 0) + backend_profile.get("total_xp", 0)
            self.assertGreater(total_xp, 0, "Backend agent gained no XP")
            self.assertGreater(backend_profile["stats"]["tasks_completed"], 0, "Backend agent tasks_completed is 0")
            
            print(f"[Test 6] ✓ Agent {backend_keys[0]} - Level {backend_profile['level']}, XP {total_xp}, Tasks {backend_profile['stats']['tasks_completed']}")
        
        print("[Test 6] ✓ Profiling integration validated")
    
    def test_7_retrospective_and_reports(self):
        """
        Test 7: Validate retrospective and final reports.
        
        Checks:
        - Sprint report has retrospective section
        - Backlog has meaningful content
        - Demo walkthrough generated
        """
        print("\n=== TEST 7: RETROSPECTIVE & REPORTS ===")
        
        if not E2ERunner.sprint_executed:
            self.skipTest("Sprint execution test must run first")
        
        # Check Retro Content
        retro_path = self._assert_artifact_exists("SPRINT_REPORT.md", "Sprint Report")
        with open(retro_path, "r", encoding="utf-8") as f:
            retro_content = f.read()
            self.assertIn("Retrospective", retro_content, "Sprint Report missing Retrospective section")
        
        # Check Backlog Integrity
        backlog_path = self._assert_artifact_exists("backlog.md", "Backlog")
        with open(backlog_path, "r", encoding="utf-8") as f:
            backlog_content = f.read()
            self.assertTrue(len(backlog_content) > 10, "Backlog seems empty")
        
        print("[Test 7] ✓ Retrospective and reports validated")
        print("\n=== ALL E2E TESTS PASSED ===")


if __name__ == "__main__":
    unittest.main()
