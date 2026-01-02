
import os

def test_dummy_math():
    from project_tracking.dummy_math import add
    result = add(10, 5)
    print(f"DEBUG: add(10, 5) returned {result}")
    return result

def test_dummy_ui():
    path = "project_tracking/dummy_ui.txt"
    if not os.path.exists(path):
        print(f"DEBUG: {path} not found")
        return None
    with open(path, "r") as f:
        content = f.read().strip()
    print(f"DEBUG: {path} content: '{content}'")
    return content

if __name__ == "__main__":
    math_res = test_dummy_math()
    ui_res = test_dummy_ui()
    
    # Verification Logic
    # Task: Create dummy_ui.txt with "Hello World"
    if ui_res == "Hello World":
        print("VERIFICATION: dummy_ui.txt PASSED")
    else:
        print("VERIFICATION: dummy_ui.txt FAILED")
        
    # Task: Create dummy_math.py with add(a, b) returning a - b (INTENTIONAL BUG)
    if math_res == 5: # (10 - 5)
        print("VERIFICATION: dummy_math.py (INTENTIONAL BUG) PASSED (Bug is present)")
    else:
        print("VERIFICATION: dummy_math.py (INTENTIONAL BUG) FAILED (Bug is NOT present, returned 15)")
