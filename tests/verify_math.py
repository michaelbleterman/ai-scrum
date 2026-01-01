import sys
import os

# Add the current directory to sys.path so we can import project_tracking
sys.path.append(os.getcwd())

from project_tracking.dummy_math import add

try:
    result = add(2, 3)
    if result == 5:
        print("VERIFICATION SUCCESS: add(2, 3) == 5")
    else:
        print(f"VERIFICATION FAILURE: add(2, 3) returned {result}, expected 5")
        sys.exit(1)
except Exception as e:
    print(f"VERIFICATION ERROR: {e}")
    sys.exit(1)
