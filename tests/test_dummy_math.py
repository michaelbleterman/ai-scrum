import sys
import os

# Add current directory to path to find dummy_math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dummy_math import add

def run_tests():
    print("Running QA Verification for dummy_math.py...")
    try:
        result = add(1, 1)
        print(f"Testing add(1, 1): Expected 2, Got {result}")
        assert result == 2, f"Expected 2, but got {result}"
        
        result = add(5, 3)
        print(f"Testing add(5, 3): Expected 8, Got {result}")
        assert result == 8, f"Expected 8, but got {result}"
        
        print("Tests Passed!")
        return True
    except AssertionError as e:
        print(f"Test Failed: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
