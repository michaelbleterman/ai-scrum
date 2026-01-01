from dummy_math import add

def test_add():
    assert add(2, 3) == 5, f"Expected 5, but got {add(2, 3)}"

if __name__ == '__main__':
    try:
        test_add()
        print("Backend Test: PASSED")
    except AssertionError as e:
        print(f"Backend Test: FAILED - {e}")
