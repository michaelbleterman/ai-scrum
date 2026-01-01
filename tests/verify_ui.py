
import os

def test_ui():
    path = "project_tracking/dummy_ui.txt"
    if not os.path.exists(path):
        print(f"FAILED: {path} not found")
        exit(1)
    
    with open(path, "r") as f:
        content = f.read().strip()
    
    if content == "Hello World":
        print("PASSED: UI text is 'Hello World'")
    else:
        print(f"FAILED: UI text is '{content}', expected 'Hello World'")
        exit(1)

if __name__ == "__main__":
    test_ui()
