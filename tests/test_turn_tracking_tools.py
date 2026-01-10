"""
Test script for turn tracking tools.
Tests the metadata parsing and update functions with real Sprint 2 data.
"""

import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sprint_metadata import parse_task_metadata, update_task_metadata_in_file

# Test 1: Parse metadata from task description
print("=== Test 1: Parse Metadata ===")
test_task = "Build user authentication API [POINTS:8|TURNS_ESTIMATED:60|TURNS_USED:47]"

points = parse_task_metadata(test_task, 'POINTS')
estimated = parse_task_metadata(test_task, 'TURNS_ESTIMATED')
used = parse_task_metadata(test_task, 'TURNS_USED')

print(f"Task: {test_task}")
print(f"Points: {points} (type: {type(points)})")
print(f"Estimated: {estimated} (type: {type(estimated)})")
print(f"Used: {used} (type: {type(used)})")
assert points == 8, f"Expected points=8, got {points}"
assert estimated == 60, f"Expected estimated=60, got {estimated}"
assert used == 47, f"Expected used=47, got {used}"
print("✅ Parse test passed!\n")

# Test 2: Parse partial metadata
print("=== Test 2: Parse Partial Metadata ===")
partial_task = "Simple fix [POINTS:2]"
points_only = parse_task_metadata(partial_task, 'POINTS')
missing = parse_task_metadata(partial_task, 'TURNS_USED', default=0)

print(f"Task: {partial_task}")
print(f"Points: {points_only}")
print(f"Missing turns_used (with default): {missing}")
assert points_only == 2
assert missing == 0
print("✅ Partial metadata test passed!\n")

# Test 3: Update metadata in test file
print("=== Test 3: Update Metadata ===")
test_sprint_file = r"C:\git\PiggyTrack\project_tracking\SPRINT_2.md"

if os.path.exists(test_sprint_file):
    # Make a backup first
    import shutil
    backup_file = test_sprint_file + ".backup_test"
    shutil.copy2(test_sprint_file, backup_file)
    print(f"Created backup: {backup_file}")
    
    # Try to update a task
    # Note: Must match file content exactly (including backticks)
    result = update_task_metadata_in_file(
        test_sprint_file,
        "Create `scripts/clean-env.sh`",  # Partial match with backticks
        {"TURNS_ESTIMATED": 25}
    )
    
    print(f"Update result: {result}")
    
    if result:
        # Read back to verify
        with open(test_sprint_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "TURNS_ESTIMATED:25" in content:
                print("✅ Metadata successfully updated in file!")
            else:
                print("❌ Metadata update failed - not found in file")
        
        # Restore from backup
        shutil.copy2(backup_file, test_sprint_file)
        os.remove(backup_file)
        print("Restored original file from backup")
    else:
        print("❌ Update failed - task not found")
        os.remove(backup_file)
else:
    print(f"⚠️  Sprint file not found: {test_sprint_file}")

print("\n=== All Tests Complete ===")
