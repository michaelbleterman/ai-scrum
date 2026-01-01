def test_ui():
    with open("project_tracking/dummy_ui.txt", "r") as f:
        content = f.read().strip()
    assert content == "Hello World", f"Expected 'Hello World', got '{content}'"

if __name__ == "__main__":
    try:
        test_ui()
        print("UI verification passed!")
    except Exception as e:
        print(f"UI verification failed: {e}")
        exit(1)
