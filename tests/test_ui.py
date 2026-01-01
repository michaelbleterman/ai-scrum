import os

def test_ui():
    path = "project_tracking/dummy_ui.txt"
    if not os.path.exists(path):
        print(f"FAIL: {path} not found")
        exit(1)
    
    with open(path, "r") as f:
        content = f.read().strip()
    
    expected = "Hello World"
    if content == expected:
        print(f"PASS: Content is '{expected}'")
        exit(0)
    else:
        print(f"FAIL: Expected '{expected}', got '{content}'")
        exit(1)

if __name__ == "__main__":
    test_ui()
