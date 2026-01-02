"""
Test script to verify model selection configuration.
"""
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from sprint_config import SprintConfig

def test_model_selection():
    """Test that model selection works correctly for all agent types."""
    print("=" * 60)
    print("Model Selection Configuration Test")
    print("=" * 60)
    
    test_cases = [
        ("orchestrator", "gemini-2.5-pro"),
        ("Orchestrator", "gemini-2.5-pro"),
        ("QA", "gemini-2.5-pro"),
        ("QA_Engineer", "gemini-2.5-pro"),
        ("qa_engineer", "gemini-2.5-pro"),
        ("Backend", "gemini-2.5-flash"),
        ("backend", "gemini-2.5-flash"),
        ("Frontend", "gemini-2.5-flash"),
        ("frontend", "gemini-2.5-flash"),
        ("DevOps", "gemini-2.5-flash"),
        ("devops", "gemini-2.5-flash"),
        ("Security", "gemini-2.5-flash"),
        ("security", "gemini-2.5-flash"),
        ("PM", "gemini-2.5-flash"),
        ("ProductManager", "gemini-2.5-flash"),
        ("productmanager", "gemini-2.5-flash"),
    ]
    
    all_passed = True
    for agent_name, expected_model in test_cases:
        actual_model = SprintConfig.get_model_for_agent(agent_name)
        passed = actual_model == expected_model
        all_passed = all_passed and passed
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} | {agent_name:20} -> {actual_model:25} (expected: {expected_model})")
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests PASSED")
        return 0
    else:
        print("✗ Some tests FAILED")
        return 1

if __name__ == "__main__":
    exit_code = test_model_selection()
    sys.exit(exit_code)
