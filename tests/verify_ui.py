import os

def verify_ui():
    path = "project_tracking/dummy_ui.txt"
    if not os.path.exists(path):
        print(f"UI Test Failed: {path} not found")
        return False
    
    with open(path, 'r') as f:
        content = f.read().strip()
        if content == "Hello World":
            print("UI Test Passed: Content is 'Hello World'")
            return True
        else:
            print(f"UI Test Failed: Content is '{content}', expected 'Hello World'")
            return False

if __name__ == "__main__":
    import sys
    if verify_ui():
        sys.exit(0)
    else:
        sys.exit(1)
