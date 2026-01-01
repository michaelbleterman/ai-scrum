
import sys
import os

# Add project_tracking to path to import dummy_math
sys.path.append(os.getcwd())
from project_tracking.dummy_math import add

def test_add():
    result = add(2, 2)
    expected = 4
    if result != expected:
        print(f"FAILED: add(2, 2) returned {result}, expected {expected}")
        sys.exit(1)
    else:
        print("PASSED: add(2, 2) returned 4")

if __name__ == "__main__":
    test_add()
