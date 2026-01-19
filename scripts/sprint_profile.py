"""
Agent Profiling Module
Manages persistent agent identities, experience (XP), levels, and statistics.
"""

import json
import os
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Simple localized profile storage
DEFAULT_PROFILE_FILE = "profiles.json"


@dataclass
class AgentProfile:
    """Represents a persistent agent identity"""
    name: str
    role: str
    level: int = 1
    xp: int = 0
    total_xp: int = 0  # Lifetime XP
    stats: Dict[str, Union[int, float]] = field(default_factory=lambda: {
        "tasks_completed": 0,
        "tasks_failed": 0,
        "turns_used": 0,
        "success_rate": 0.0
    })
    skills: List[str] = field(default_factory=list)
    last_active: str = ""

    def add_xp(self, points: int):
        """Add XP and handle leveling up"""
        self.xp += points
        self.total_xp += points
        
        # Simple leveling curve: Level * 100 XP to next level
        xp_needed = self.level * 100
        while self.xp >= xp_needed:
            self.xp -= xp_needed
            self.level += 1
            xp_needed = self.level * 100
            
    def record_task_completion(self, success: bool, turns: int):
        """Update stats after a task"""
        if success:
            self.stats["tasks_completed"] += 1
        else:
            self.stats["tasks_failed"] += 1
            
        self.stats["turns_used"] += turns
        
        total = self.stats["tasks_completed"] + self.stats["tasks_failed"]
        if total > 0:
            self.stats["success_rate"] = round(self.stats["tasks_completed"] / total, 2)
            
        self.last_active = datetime.now().isoformat()


class ProfileManager:
    """Manages loading and saving of agent profiles"""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.file_path = os.path.join(storage_dir, DEFAULT_PROFILE_FILE)
        self.profiles: Dict[str, AgentProfile] = {}
        self.load()
        
    def load(self):
        """Load profiles from disk"""
        if not os.path.exists(self.file_path):
            return
            
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for name, p_data in data.items():
                    self.profiles[name] = AgentProfile(**p_data)
        except Exception as e:
            print(f"Error loading profiles: {e}")
            
    def save(self):
        """Save profiles to disk"""
        try:
            data = {name: asdict(p) for name, p in self.profiles.items()}
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")
            
    def get_profile(self, name: str, role: str = "General") -> AgentProfile:
        """Get or create a profile"""
        if name not in self.profiles:
            self.profiles[name] = AgentProfile(name=name, role=role)
        return self.profiles[name]
        
    def update_profile(self, name: str, xp_gain: int, success: bool, turns: int):
        """Update a profile after task completion"""
        profile = self.get_profile(name)
        profile.add_xp(xp_gain)
        profile.record_task_completion(success, turns)
        self.save()

if __name__ == "__main__":
    # Test
    pm = ProfileManager(".")
    p = pm.get_profile("TestAgent", "Tester")
    p.add_xp(150)
    print(f"Level: {p.level}, XP: {p.xp}")
