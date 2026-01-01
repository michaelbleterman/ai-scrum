import sys
from dummy_math import add

def test_add():
    result = add(2, 2)
    expected = 4
    if result == expected:
        print("PASS: add(2, 2) == 4")
        sys.exit(0)
    else:
        print(f"FAIL: add(2, 2) expected {expected}, got {result}")
        sys.exit(1)

if __name__ == "__main__":
    test_add()
