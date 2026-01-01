import sys
import os

# Add current directory to path so we can import dummy_math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dummy_math import add

try:
    result = add(1, 1)
    if result == 2:
        print("PASS: add(1, 1) == 2")
        sys.exit(0)
    else:
        print(f"FAIL: add(1, 1) expected 2, got {result}")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
