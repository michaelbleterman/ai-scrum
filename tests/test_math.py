from project_tracking.dummy_math import add

def test_add():
    assert add(1, 1) == 2, f"Expected 2, got {add(1, 1)}"
    assert add(5, 3) == 8, f"Expected 8, got {add(5, 3)}"

if __name__ == "__main__":
    try:
        test_add()
        print("Math verification passed!")
    except AssertionError as e:
        print(f"Math verification failed: {e}")
        exit(1)
