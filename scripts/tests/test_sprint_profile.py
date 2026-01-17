import unittest
import sys
import os
import shutil
import tempfile
from datetime import datetime

# Add scripts dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sprint_profile import AgentProfile, ProfileManager

class TestAgentProfile(unittest.TestCase):
    
    def test_leveling_up(self):
        p = AgentProfile("TestBot", "Tester")
        self.assertEqual(p.level, 1)
        self.assertEqual(p.xp, 0)
        
        # Level 1 requires 100 XP
        p.add_xp(50)
        self.assertEqual(p.level, 1)
        self.assertEqual(p.xp, 50)
        
        p.add_xp(60) # Total 110, should be Level 2 with 10 XP
        self.assertEqual(p.level, 2)
        self.assertEqual(p.xp, 10)
        self.assertEqual(p.total_xp, 110)
        
    def test_stats_update(self):
        p = AgentProfile("TestBot", "Tester")
        
        p.record_task_completion(success=True, turns=10)
        self.assertEqual(p.stats["tasks_completed"], 1)
        self.assertEqual(p.stats["turns_used"], 10)
        self.assertEqual(p.stats["success_rate"], 1.0)
        
        p.record_task_completion(success=False, turns=5)
        self.assertEqual(p.stats["tasks_failed"], 1)
        self.assertEqual(p.stats["success_rate"], 0.5)

class TestProfileManager(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pm = ProfileManager(self.test_dir)
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_persistence(self):
        # Create and Save
        p = self.pm.get_profile("SaverBot", "Saver")
        p.add_xp(200)
        self.pm.save()
        
        # Reload
        pm2 = ProfileManager(self.test_dir)
        p2 = pm2.get_profile("SaverBot")
        
        self.assertEqual(p2.level, 2) # 0->100(L2), need 200 more for L3. Total 200XP ends at L2.
        self.assertEqual(p2.role, "Saver")
        
    def test_update_workflow(self):
        self.pm.update_profile("WorkerBot", xp_gain=150, success=True, turns=20)
        
        p = self.pm.get_profile("WorkerBot")
        self.assertEqual(p.level, 2)
        self.assertEqual(p.stats["tasks_completed"], 1)

if __name__ == "__main__":
    unittest.main()
