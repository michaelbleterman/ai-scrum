
import sys
import os

# Set base dir to the directory where this script is located
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

def test_math():
    print("Testing dummy_math.py...")
    try:
        from dummy_math import add
        result = add(2, 3)
        if result == 5:
            print("[PASS] add(2, 3) == 5")
            return True
        else:
            print(f"[FAIL] add(2, 3) returned {result}, expected 5")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_ui():
    print("Testing dummy_ui.txt...")
    ui_path = os.path.join(base_dir, "dummy_ui.txt")
    try:
        if not os.path.exists(ui_path):
            print(f"[FAIL] {ui_path} does not exist")
            return False
        with open(ui_path, "r") as f:
            content = f.read().strip()
            if content == "Hello World":
                print("[PASS] content matches 'Hello World'")
                return True
            else:
                print(f"[FAIL] content was '{content}', expected 'Hello World'")
                return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    math_ok = test_math()
    ui_ok = test_ui()
    
    if not math_ok or not ui_ok:
        sys.exit(1)
    else:
        sys.exit(0)
