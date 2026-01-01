import os
import sys

# Add project_tracking to sys.path
sys.path.append(os.path.join(os.getcwd(), 'project_tracking'))

try:
    from dummy_math import add
except ImportError as e:
    print(f"FAILED: Could not import dummy_math: {e}")
    sys.exit(1)

def test_add():
    try:
        result = add(2, 3)
        if result == 5:
            print("PASS: add(2, 3) == 5")
            return True
        else:
            print(f"FAIL: add(2, 3) returned {result}, expected 5")
            return False
    except Exception as e:
        print(f"FAIL: add(2, 3) raised exception: {e}")
        return False

def test_ui():
    ui_path = "project_tracking/dummy_ui.txt"
    if not os.path.exists(ui_path):
        print(f"FAIL: {ui_path} does not exist")
        return False
    
    with open(ui_path, "r") as f:
        content = f.read().strip()
    
    if content == "Hello World":
        print("PASS: dummy_ui.txt contains 'Hello World'")
        return True
    else:
        print(f"FAIL: dummy_ui.txt contains '{content}', expected 'Hello World'")
        return False

if __name__ == "__main__":
    math_pass = test_add()
    ui_pass = test_ui()
    
    if math_pass and ui_pass:
        sys.exit(0)
    else:
        sys.exit(1)
